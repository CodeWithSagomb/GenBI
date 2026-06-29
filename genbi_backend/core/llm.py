import asyncio
import json
import re
from pathlib import Path
from typing import Optional

import litellm

from config import settings
from core.exceptions import LLMTimeoutError
from core.column_classifier import annotate_column_types

# Désactive les logs verbeux de LiteLLM
litellm.suppress_debug_info = True

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _replace_millions_fcfa(text: str) -> str:
    """Convertit 'X,Y millions FCFA' → chiffres complets avec espaces.

    Le LLM écrit parfois 'millions' pour les grands montants malgré les règles.
    Ce post-processing garantit le format correct indépendamment de la réponse LLM.
    Exemples :
      "4,5 millions FCFA"  → "4 500 000 FCFA"
      "3 millions de FCFA" → "3 000 000 FCFA"
      "1,23 millions FCFA" → "1 230 000 FCFA"
    """
    def _with_decimal(m: re.Match) -> str:
        integer_part = int(m.group(1))
        decimal_str  = m.group(2).ljust(6, "0")[:6]
        total = integer_part * 1_000_000 + int(decimal_str)
        return f"{total:,}".replace(",", " ") + " FCFA"

    def _integer_only(m: re.Match) -> str:
        total = int(m.group(1)) * 1_000_000
        return f"{total:,}".replace(",", " ") + " FCFA"

    text = re.sub(
        r"(\d+)[,.](\d+)\s+millions?\s+(?:de\s+)?FCFA",
        _with_decimal, text, flags=re.IGNORECASE,
    )
    text = re.sub(
        r"(\d+)\s+millions?\s+(?:de\s+)?FCFA",
        _integer_only, text, flags=re.IGNORECASE,
    )
    return text


def _clean_sql(raw: str) -> str:
    """Extrait le SQL pur d'une réponse LLM potentiellement enveloppée en markdown.

    Supprime les blocs ```sql ... ```, les commentaires SQL (-- et /* */),
    le texte avant le premier SELECT, et les point-virgules finaux.
    """
    raw = raw.strip()
    # Retire les blocs de code markdown
    raw = re.sub(r"^```(?:sql)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```\s*$", "", raw)
    # Supprime les commentaires SQL — ils peuvent contenir des apostrophes françaises
    # qui cassent le tokenizer sqlglot (ex: -- Note: c'est la table X)
    raw = re.sub(r"--[^\n]*", "", raw)
    raw = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)
    # Extrait uniquement depuis le premier SELECT (ignore le texte introductif)
    select_match = re.search(r"\bSELECT\b", raw, re.IGNORECASE)
    if select_match:
        raw = raw[select_match.start():]
    # Tronque au premier point-virgule (supprime tout texte explicatif après la requête)
    semi_match = re.search(r";", raw)
    if semi_match:
        raw = raw[:semi_match.start()]
    # Remplace les apostrophes françaises dans les identifiants SQL
    # Ex: AS jours_jusqu'à_expiration → AS jours_jusqu_à_expiration
    # Sûr : \w'\w ne matche pas les délimiteurs de chaînes SQL 'Tiers-Payant'
    raw = re.sub(r"(\w)'(\w)", r"\1_\2", raw)
    # Retire les point-virgules finaux et les espaces résiduels
    raw = raw.rstrip(";").strip()
    return raw


def load_prompt(name: str) -> str:
    """Lit un template de prompt versionné depuis core/prompts/."""
    path = _PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt introuvable : {path}")
    return path.read_text(encoding="utf-8")


def build_sql_prompt(
    schema: str,
    question: str,
    examples: list | None = None,
    semantic_context: str = "",
    extra_reminder: str = "",
) -> str:
    """Construit le prompt pour la génération SQL.

    - examples        : paires Question→SQL issues du RAG (bloc <examples>)
    - semantic_context: définitions détectées par la couche sémantique (bloc <semantic_context>)
      Injecté uniquement si le template contient le placeholder — rétrocompatible v1.
    """
    template = load_prompt(settings.SQL_PROMPT_VERSION)
    examples_block = ""
    if examples:
        lines = "\n".join(
            f"Question: {ex['question']}\nSQL: {ex['sql']}" for ex in examples
        )
        examples_block = f"\n<examples>\n{lines}\n</examples>"
    fmt_kwargs = {"schema": schema, "question": question, "examples": examples_block}
    if "{semantic_context}" in template:
        fmt_kwargs["semantic_context"] = semantic_context
    prompt = template.format(**fmt_kwargs)
    # Inject critical reminders right before <question> so they sit in high-recency context.
    # RAG examples can pull old patterns — these reminders override them.
    _reminders: list[str] = []
    _margin_kw = ("marge", "rentab", "profitable", "profit", "margin")
    if any(kw in question.lower() for kw in _margin_kw):
        _reminders.append(
            "RAPPEL CRITIQUE MARGE : 2 tables UNIQUEMENT — FROM marts.fct_purchases fp "
            "JOIN marts.dim_products pd ON fp.product_id = pd.product_id — "
            "formule SUM((pd.public_price_fcfa - fp.purchase_price_fcfa) * fp.quantity_ordered) — "
            "quantity_ordered OBLIGATOIRE — "
            "JAMAIS fct_sales (pas même en sous-requête ou JOIN) — "
            "JAMAIS stg_raw__sale_details — aucune autre table supplémentaire."
        )
    _insured_kw = ("assurée", "assurées", "assurés", "insured", "non assur")
    if any(kw in question.lower() for kw in _insured_kw):
        _reminders.append(
            "RAPPEL CRITIQUE ASSURÉES : utiliser client_type avec GROUP BY — "
            "SELECT client_type, COUNT(*) AS nb_ventes, SUM(total_amount_fcfa) AS ca_fcfa "
            "FROM marts.fct_sales GROUP BY client_type ORDER BY client_type — "
            "JAMAIS insurer_id IS NOT NULL — JAMAIS JOIN dim_insurers — "
            "JAMAIS patient_share_fcfa — JAMAIS SUM(CASE WHEN insurer_id...)."
        )
    _evolution_kw = ("évolue", "évolution", "evolve", "evolution", "over the month",
                     "per month", "by month", "monthly", "par mois", "tendance", "trend")
    if any(kw in question.lower() for kw in _evolution_kw):
        _reminders.append(
            "RAPPEL CRITIQUE ÉVOLUTION : 2 colonnes UNIQUEMENT — "
            "SELECT sale_month AS mois, SUM(total_amount_fcfa) AS total_revenue "
            "FROM marts.fct_sales GROUP BY sale_month ORDER BY sale_month — "
            "JAMAIS ajouter COUNT(*) dans une évolution de CA — "
            "COUNT uniquement si la question porte EXPLICITEMENT sur le nombre de transactions."
        )
    if extra_reminder:
        _reminders.append(extra_reminder)
    if _reminders:
        block = "\n" + "\n".join(_reminders) + "\n"
        prompt = prompt.replace("<question>", block + "<question>", 1)
    return prompt


_LANG_RULES_FR = """\
- LANGUE : Tout en français. JAMAIS de mots anglais (quarter, orders, sales, best, revenue, trend, breakdown).
- COMMANDES/ACHATS : utiliser "commandes" pour les fournisseurs/approvisionnements — jamais "ventes", "transactions", "orders".
  ✓  "UBIPHARM Sénégal a passé le plus de commandes avec 10 commandes."
  ✗  "UBIPHARM Sénégal a le plus d'orders avec 10 transactions."
- MONTANTS FCFA : toujours écrire en chiffres complets avec espaces comme séparateurs de milliers — JAMAIS en millions.
  ✓  "Le montant total est de 2 530 000 FCFA."
  ✗  "Le montant total est de 2,5 millions FCFA."  ✗  "2 millions de FCFA"
- MOIS FR : 1=janvier · 2=février · 3=mars · 4=avril · 5=mai · 6=juin · 7=juillet · 8=août · 9=septembre · 10=octobre · 11=novembre · 12=décembre. Mois 2 = février (jamais janvier)."""

_LANG_RULES_EN = """\
- LANGUAGE: Write entirely in English. Never mix French words into the insight.
- MONTHS EN: 1=January · 2=February · 3=March · 4=April · 5=May · 6=June · 7=July · 8=August · 9=September · 10=October · 11=November · 12=December.
- SUPPLIERS/ORDERS: use "orders" for supplier purchases — never "ventes", "transactions".
  ✓  "UBIPHARM Sénégal placed the most orders with 10 orders."
- AMOUNTS: always cite FCFA amounts in full with spaces as thousand separators (e.g., 16 530 900 FCFA).
- STOCKOUTS: use "stockouts" or "missed sales" — never "ruptures" or "ventes manquées"."""


def build_insight_prompt(question: str, results: dict, language: str = 'fr') -> str:
    """Construit le prompt pour la génération d'insight.

    Annote les types de colonnes avant sérialisation pour guider le LLM
    et éviter les hallucinations de montants FCFA sur des colonnes COUNT.
    Injecte des règles linguistiques séparées selon fr/en pour éviter les conflits.
    """
    template = load_prompt("v1_insight_generation")
    columns = results.get("columns", [])
    annotations = annotate_column_types(columns)
    data_str = json.dumps(results, ensure_ascii=False, indent=2)
    enriched = f"Types de colonnes:\n{annotations}\n\nDonnées:\n{data_str}"
    lang_label = "français" if language == 'fr' else "English"
    lang_rules = _LANG_RULES_FR if language == 'fr' else _LANG_RULES_EN
    return template.format(question=question, results=enriched, language=lang_label, lang_rules=lang_rules)


async def generate_sql(
    schema: str,
    question: str,
    examples: list | None = None,
    semantic_context: str = "",
    conversation_history: list | None = None,
    timeout: Optional[int] = None,
    extra_reminder: str = "",
) -> str:
    """Appelle Ollama pour générer un SELECT SQL.

    temperature=0.0 pour le déterminisme.
    conversation_history : liste de dicts {role, content} — turns précédents injectés
    en multi-turn natif LiteLLM pour le chat multi-tour (Phase 4).
    extra_reminder : hint injecté par la validation sémantique pour corriger le SQL.
    Lève LLMTimeoutError si Ollama ne répond pas dans le délai imparti.
    """
    timeout_s = timeout if timeout is not None else settings.LLM_SQL_TIMEOUT
    prompt = build_sql_prompt(schema, question, examples, semantic_context, extra_reminder)
    messages: list[dict] = []
    if conversation_history:
        for turn in conversation_history[-6:]:
            messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": prompt})
    try:
        response = await asyncio.wait_for(
            litellm.acompletion(
                model=f"ollama/{settings.OLLAMA_MODEL}",
                messages=messages,
                temperature=0.0,
                api_base=settings.OLLAMA_BASE_URL,
            ),
            timeout=float(timeout_s),
        )
    except (asyncio.TimeoutError, TimeoutError):
        raise LLMTimeoutError(
            f"Ollama n'a pas répondu en {timeout_s}s. Réessayez dans quelques instants."
        )
    return _clean_sql(response.choices[0].message.content)


def build_repair_prompt(
    schema: str, question: str, failed_sql: str, error_message: str
) -> str:
    """Construit le prompt de réparation SQL (Phase 1 — MARS-SQL)."""
    template = load_prompt("v1_sql_repair")
    return template.format(
        schema=schema,
        question=question,
        failed_sql=failed_sql,
        error_message=error_message,
    )


async def repair_sql(
    schema: str,
    question: str,
    failed_sql: str,
    error_message: str,
    timeout: Optional[int] = None,
) -> str:
    """Demande au LLM de corriger un SQL qui a échoué (execution-feedback loop).

    Lève LLMTimeoutError si Ollama ne répond pas dans le délai imparti.
    """
    timeout_s = timeout if timeout is not None else settings.SQL_REPAIR_TIMEOUT
    prompt = build_repair_prompt(schema, question, failed_sql, error_message)
    try:
        response = await asyncio.wait_for(
            litellm.acompletion(
                model=f"ollama/{settings.OLLAMA_MODEL}",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                api_base=settings.OLLAMA_BASE_URL,
            ),
            timeout=float(timeout_s),
        )
    except (asyncio.TimeoutError, TimeoutError):
        raise LLMTimeoutError(
            f"Ollama n'a pas répondu en {timeout_s}s (repair). Réessayez dans quelques instants."
        )
    return _clean_sql(response.choices[0].message.content)


async def generate_insight(
    question: str, results: dict, timeout: Optional[int] = None, language: str = 'fr'
) -> str:
    """Appelle Ollama pour rédiger un insight en français.

    temperature=0.1 pour un bon équilibre style naturel / respect strict des règles de formatage.
    Lève LLMTimeoutError si Ollama ne répond pas dans le délai imparti.
    """
    timeout_s = timeout if timeout is not None else settings.LLM_INSIGHT_TIMEOUT
    prompt = build_insight_prompt(question, results, language=language)
    try:
        response = await asyncio.wait_for(
            litellm.acompletion(
                model=f"ollama/{settings.OLLAMA_MODEL}",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                api_base=settings.OLLAMA_BASE_URL,
            ),
            timeout=float(timeout_s),
        )
    except (asyncio.TimeoutError, TimeoutError):
        raise LLMTimeoutError(
            f"Ollama n'a pas répondu en {timeout_s}s. Réessayez dans quelques instants."
        )
    insight = response.choices[0].message.content.strip()
    return _replace_millions_fcfa(insight)


async def generate_insight_stream(
    question: str, results: dict, timeout: Optional[int] = None, language: str = 'fr'
):
    """Version streaming de generate_insight — async generator qui yield des tokens.

    Yield chaque token brut au fil de la génération.
    Retourne l'insight complet post-processé (_replace_millions_fcfa) via StopIteration.value
    ou via le dernier yield de type sentinel — l'appelant lit `full_insight` après épuisement.

    Usage :
        buffer = ""
        gen = generate_insight_stream(q, results, language=language)
        async for token in gen:
            buffer += token
            yield token   # stream vers le client
        corrected = _replace_millions_fcfa(buffer.strip())
    """
    timeout_s = timeout if timeout is not None else settings.LLM_INSIGHT_TIMEOUT
    prompt = build_insight_prompt(question, results, language=language)
    try:
        response = await asyncio.wait_for(
            litellm.acompletion(
                model=f"ollama/{settings.OLLAMA_MODEL}",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                stream=True,
                api_base=settings.OLLAMA_BASE_URL,
            ),
            timeout=float(timeout_s),
        )
    except (asyncio.TimeoutError, TimeoutError):
        raise LLMTimeoutError(
            f"Ollama n'a pas répondu en {timeout_s}s. Réessayez dans quelques instants."
        )
    async for chunk in response:
        token = chunk.choices[0].delta.content or ""
        if token:
            yield token
