import asyncio
import json
from pathlib import Path

import litellm

from config import settings
from core.exceptions import LLMTimeoutError

# Désactive les logs verbeux de LiteLLM
litellm.suppress_debug_info = True

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    """Lit un template de prompt versionné depuis core/prompts/."""
    path = _PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt introuvable : {path}")
    return path.read_text(encoding="utf-8")


def build_sql_prompt(schema: str, question: str) -> str:
    """Construit le prompt pour la génération SQL."""
    template = load_prompt("v1_sql_generation")
    return template.format(schema=schema, question=question)


def build_insight_prompt(question: str, results: dict) -> str:
    """Construit le prompt pour la génération d'insight."""
    template = load_prompt("v1_insight_generation")
    results_str = json.dumps(results, ensure_ascii=False, indent=2)
    return template.format(question=question, results=results_str)


async def generate_sql(schema: str, question: str, timeout: int | None = None) -> str:
    """Appelle Ollama pour générer un SELECT SQL.

    temperature=0.0 pour le déterminisme.
    Lève LLMTimeoutError si Ollama ne répond pas dans le délai imparti.
    """
    timeout_s = timeout if timeout is not None else settings.LLM_SQL_TIMEOUT
    prompt = build_sql_prompt(schema, question)
    try:
        async with asyncio.timeout(timeout_s):
            response = await litellm.acompletion(
                model=f"ollama/{settings.OLLAMA_MODEL}",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                api_base=settings.OLLAMA_BASE_URL,
            )
    except TimeoutError:
        raise LLMTimeoutError(
            f"Ollama n'a pas répondu en {timeout_s}s. Réessayez dans quelques instants."
        )
    return response.choices[0].message.content.strip()


async def generate_insight(
    question: str, results: dict, timeout: int | None = None
) -> str:
    """Appelle Ollama pour rédiger un insight en français.

    temperature=0.3 pour un style plus naturel.
    Lève LLMTimeoutError si Ollama ne répond pas dans le délai imparti.
    """
    timeout_s = timeout if timeout is not None else settings.LLM_INSIGHT_TIMEOUT
    prompt = build_insight_prompt(question, results)
    try:
        async with asyncio.timeout(timeout_s):
            response = await litellm.acompletion(
                model=f"ollama/{settings.OLLAMA_MODEL}",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                api_base=settings.OLLAMA_BASE_URL,
            )
    except TimeoutError:
        raise LLMTimeoutError(
            f"Ollama n'a pas répondu en {timeout_s}s. Réessayez dans quelques instants."
        )
    return response.choices[0].message.content.strip()
