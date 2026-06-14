"""Filtrage dynamique du schéma avant construction du prompt SQL.

Inspiration : AP-SQL (arxiv 2506.03598) + Bidirectional Schema Linking (arxiv 2510.14296)

Stratégie hybride :
  1. Tables core toujours incluses (couverture minimale garantie)
  2. Score = 0.3 × lexical + 0.7 × cosine(nomic-embed-text)
  3. Fallback schéma complet si embeddings indisponibles
"""
import logging
import re
from typing import Optional

from core.rag import _embed

logger = logging.getLogger(__name__)

# Toujours incluses — jointures implicites quasi systématiques
_CORE_TABLES = frozenset({
    "marts.fct_sales",
    "marts.dim_products",
    "staging.stg_raw__sale_details",
})


def parse_schema_to_records(schema_text: str) -> list[dict]:
    """Transforme le schéma compact en liste de records {table, columns, line}."""
    records = []
    for line in schema_text.strip().split("\n"):
        if ":" not in line:
            continue
        table, cols = line.split(":", 1)
        records.append({
            "table": table.strip(),
            "columns": cols.strip(),
            "line": line.strip(),
        })
    return records


def precompute_schema_embeddings(schema_text: str) -> Optional[dict[str, list[float]]]:
    """Pré-calcule les embeddings nomic-embed-text pour chaque table du schéma.

    Appelé une seule fois au démarrage (lifespan). Retourne None si Ollama
    est indisponible — le filtre utilisera le schéma complet en fallback.
    """
    records = parse_schema_to_records(schema_text)
    embeddings: dict[str, list[float]] = {}
    try:
        for rec in records:
            text = f"{rec['table']} {rec['columns']}"
            vec = _embed(text)
            if vec is not None:
                embeddings[rec["table"]] = vec
        logger.info("Schema embeddings pré-calculés : %d tables", len(embeddings))
        return embeddings
    except Exception as exc:
        logger.warning("Schema embeddings non disponibles (best-effort) : %s", exc)
        return None


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def _lexical_score(q_tokens: set[str], table: str, columns: str) -> float:
    """Recouvrement de tokens entre la question et les identifiants de la table."""
    table_tokens = set(re.findall(r"[a-z]+", f"{table} {columns}".lower()))
    if not q_tokens:
        return 0.0
    return len(q_tokens & table_tokens) / len(q_tokens)


def filter_schema_for_question(
    schema_text: str,
    question: str,
    schema_embeddings: Optional[dict[str, list[float]]],
    top_k: int = 15,
) -> str:
    """Retourne le schéma filtré aux top_k tables les plus pertinentes.

    Si schema_embeddings est None ou si l'embedding de la question échoue,
    retourne le schéma complet (comportement identique à avant Phase 3).
    """
    if schema_embeddings is None:
        return schema_text

    try:
        q_vec = _embed(question)
    except Exception:
        return schema_text
    if q_vec is None:
        return schema_text

    records = parse_schema_to_records(schema_text)
    q_tokens = set(re.findall(r"[a-z]+", question.lower()))

    scored: list[tuple[str, float]] = []
    for rec in records:
        table = rec["table"]
        if table in _CORE_TABLES:
            scored.append((rec["line"], float("inf")))
            continue
        lex = _lexical_score(q_tokens, table, rec["columns"])
        t_vec = schema_embeddings.get(table)
        sem = _cosine(q_vec, t_vec) if t_vec is not None else 0.0
        scored.append((rec["line"], 0.3 * lex + 0.7 * sem))

    scored.sort(key=lambda x: x[1], reverse=True)
    return "\n".join(line for line, _ in scored[:top_k])
