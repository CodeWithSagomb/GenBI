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
    return template.format(**fmt_kwargs)


def build_insight_prompt(question: str, results: dict, language: str = 'fr') -> str:
    """Construit le prompt pour la génération d'insight.

    Annote les types de colonnes avant sérialisation pour guider le LLM
    et éviter les hallucinations de montants FCFA sur des colonnes COUNT.
    """
    template = load_prompt("v1_insight_generation")
    columns = results.get("columns", [])
    annotations = annotate_column_types(columns)
    data_str = json.dumps(results, ensure_ascii=False, indent=2)
    enriched = f"Types de colonnes:\n{annotations}\n\nDonnées:\n{data_str}"
    lang_label = "français" if language == 'fr' else "English"
    return template.format(question=question, results=enriched, language=lang_label)


async def generate_sql(
    schema: str,
    question: str,
    examples: list | None = None,
    semantic_context: str = "",
    conversation_history: list | None = None,
    timeout: Optional[int] = None,
) -> str:
    """Appelle Ollama pour générer un SELECT SQL.

    temperature=0.0 pour le déterminisme.
    conversation_history : liste de dicts {role, content} — turns précédents injectés
    en multi-turn natif LiteLLM pour le chat multi-tour (Phase 4).
    Lève LLMTimeoutError si Ollama ne répond pas dans le délai imparti.
    """
    timeout_s = timeout if timeout is not None else settings.LLM_SQL_TIMEOUT
    prompt = build_sql_prompt(schema, question, examples, semantic_context)
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

    temperature=0.3 pour un style plus naturel.
    Lève LLMTimeoutError si Ollama ne répond pas dans le délai imparti.
    """
    timeout_s = timeout if timeout is not None else settings.LLM_INSIGHT_TIMEOUT
    prompt = build_insight_prompt(question, results, language=language)
    try:
        response = await asyncio.wait_for(
            litellm.acompletion(
                model=f"ollama/{settings.OLLAMA_MODEL}",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                api_base=settings.OLLAMA_BASE_URL,
            ),
            timeout=float(timeout_s),
        )
    except (asyncio.TimeoutError, TimeoutError):
        raise LLMTimeoutError(
            f"Ollama n'a pas répondu en {timeout_s}s. Réessayez dans quelques instants."
        )
    return response.choices[0].message.content.strip()
