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

    Supprime les blocs ```sql ... ``` ou ``` ... ```, puis les point-virgules
    finaux afin d'éviter les faux positifs du validateur et les conflits avec
    la pagination ajoutée en aval.
    """
    raw = raw.strip()
    # Retire les blocs de code markdown
    raw = re.sub(r"^```(?:sql)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```\s*$", "", raw)
    # Retire les point-virgules finaux
    raw = raw.rstrip(";").strip()
    return raw


def load_prompt(name: str) -> str:
    """Lit un template de prompt versionné depuis core/prompts/."""
    path = _PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt introuvable : {path}")
    return path.read_text(encoding="utf-8")


def build_sql_prompt(schema: str, question: str, examples: list | None = None) -> str:
    """Construit le prompt pour la génération SQL.

    Si `examples` est fourni (paires Question→SQL issues du RAG), un bloc
    <examples> est injecté dans le prompt pour guider le LLM.
    """
    template = load_prompt("v1_sql_generation")
    examples_block = ""
    if examples:
        lines = "\n".join(
            f"Question: {ex['question']}\nSQL: {ex['sql']}" for ex in examples
        )
        examples_block = f"\n<examples>\n{lines}\n</examples>"
    return template.format(schema=schema, question=question, examples=examples_block)


def build_insight_prompt(question: str, results: dict) -> str:
    """Construit le prompt pour la génération d'insight.

    Annote les types de colonnes avant sérialisation pour guider le LLM
    et éviter les hallucinations de montants FCFA sur des colonnes COUNT.
    """
    template = load_prompt("v1_insight_generation")
    columns = results.get("columns", [])
    annotations = annotate_column_types(columns)
    data_str = json.dumps(results, ensure_ascii=False, indent=2)
    enriched = f"Types de colonnes:\n{annotations}\n\nDonnées:\n{data_str}"
    return template.format(question=question, results=enriched)


async def generate_sql(
    schema: str,
    question: str,
    examples: list | None = None,
    timeout: Optional[int] = None,
) -> str:
    """Appelle Ollama pour générer un SELECT SQL.

    temperature=0.0 pour le déterminisme.
    Lève LLMTimeoutError si Ollama ne répond pas dans le délai imparti.
    """
    timeout_s = timeout if timeout is not None else settings.LLM_SQL_TIMEOUT
    prompt = build_sql_prompt(schema, question, examples)
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
            f"Ollama n'a pas répondu en {timeout_s}s. Réessayez dans quelques instants."
        )
    return _clean_sql(response.choices[0].message.content)


async def generate_insight(
    question: str, results: dict, timeout: Optional[int] = None
) -> str:
    """Appelle Ollama pour rédiger un insight en français.

    temperature=0.3 pour un style plus naturel.
    Lève LLMTimeoutError si Ollama ne répond pas dans le délai imparti.
    """
    timeout_s = timeout if timeout is not None else settings.LLM_INSIGHT_TIMEOUT
    prompt = build_insight_prompt(question, results)
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
