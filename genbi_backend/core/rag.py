"""RAG few-shot : index et retrouve des paires Question→SQL dans ChromaDB."""
import logging
from typing import Optional

import litellm

from config import settings

logger = logging.getLogger(__name__)

_EMBED_MODEL = "ollama/nomic-embed-text"


def get_collection(client, pharmacy_id: int):
    """Retourne (ou crée) la collection ChromaDB isolée pour cette pharmacie."""
    return client.get_or_create_collection(
        name=f"pharmacy_{pharmacy_id}",
        metadata={"hnsw:space": "cosine"},
    )


def _embed(text: str) -> Optional[list[float]]:
    response = litellm.embedding(_EMBED_MODEL, input=[text], api_base=settings.OLLAMA_BASE_URL)
    return response.data[0]["embedding"]


def index_example(client, pharmacy_id: int, question: str, sql: str) -> None:
    """Indexe une paire Question→SQL validée. Best-effort : les erreurs sont loggées."""
    try:
        vector = _embed(question)
        col = get_collection(client, pharmacy_id)
        doc_id = f"{pharmacy_id}_{abs(hash(question))}"
        col.upsert(
            ids=[doc_id],
            embeddings=[vector],
            documents=[question],
            metadatas=[{"sql": sql, "question": question}],
        )
    except Exception as exc:
        logger.warning("RAG index_example failed (best-effort): %s", exc)


def seed_collection(client, pharmacy_id: int, examples: list[dict]) -> int:
    """Injecte les exemples golden dans ChromaDB si la collection est vide.

    Chaque exemple doit avoir les clés 'question' et 'golden_sql'.
    Retourne le nombre d'exemples indexés (0 si la collection était déjà peuplée).
    """
    col = get_collection(client, pharmacy_id)
    if col.count() > 0:
        return 0
    count = 0
    for ex in examples:
        try:
            index_example(client, pharmacy_id, ex["question"], ex["golden_sql"])
            count += 1
        except Exception as exc:
            logger.warning("RAG seed skipped (best-effort): %s", exc)
    return count


def retrieve_examples(client, pharmacy_id: int, question: str, n: int = 3) -> list[dict]:
    """Retourne les n exemples les plus proches. Retourne [] si ChromaDB ou embedding indisponible."""
    try:
        col = get_collection(client, pharmacy_id)
        if col.count() == 0:
            return []
        vector = _embed(question)
        results = col.query(
            query_embeddings=[vector],
            n_results=min(n, col.count()),
            include=["metadatas"],
        )
        return [
            {"question": m["question"], "sql": m["sql"]}
            for m in results["metadatas"][0]
        ]
    except Exception as exc:
        logger.warning("RAG retrieve_examples failed (best-effort): %s", exc)
        return []
