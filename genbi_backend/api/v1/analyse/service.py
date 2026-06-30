from typing import Optional

import psycopg2

from api.v1.query.service import query_pipeline
from core.exceptions import DatabaseError
from core.pagination import PageParams
from core.rules_loader import rules

_DEFAULT_PAGE = PageParams(limit=100, offset=0)


def detect_sub_questions(question: str) -> Optional[list[str]]:
    """Retourne la liste de sous-questions si la question est composée, sinon None."""
    for pattern, sub_questions in rules.compiled_patterns:
        if pattern.search(question):
            return sub_questions
    return None


async def _run_sub_query(
    question: str,
    schema: str,
    pool,
    pharmacy_id: int,
    with_insight: bool = False,
    rag_client=None,
    semantic_catalog: dict | None = None,
    schema_embeddings: dict | None = None,
    conversation_history: list | None = None,
    language: str = 'fr',
) -> dict:
    """Exécute une sous-question sur une connexion dédiée du pool."""
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SET app.current_pharmacy_id = %s", (pharmacy_id,))
        conn.commit()
        return await query_pipeline(
            question, schema, conn, _DEFAULT_PAGE,
            with_insight=with_insight,
            rag_client=rag_client,
            pharmacy_id=pharmacy_id,
            semantic_catalog=semantic_catalog,
            schema_embeddings=schema_embeddings,
            conversation_history=conversation_history,
            language=language,
        )
    except psycopg2.Error as e:
        conn.rollback()
        raise DatabaseError(f"Erreur DB : {e}") from e
    finally:
        try:
            with conn.cursor() as cur:
                cur.execute("RESET app.current_pharmacy_id")
            conn.commit()
        except Exception:
            pass
        pool.putconn(conn)


async def analyse_pipeline(
    question: str,
    schema: str,
    pool,
    pharmacy_id: int,
    rag_client=None,
    semantic_catalog: dict | None = None,
    schema_embeddings: dict | None = None,
    conversation_history: list | None = None,
    language: str = 'fr',
) -> dict:
    """
    Route la question vers le bon pipeline :
    - Composée : sous-questions exécutées séquentiellement (Ollama mono-thread),
                 sans insight individuel pour éviter les timeouts
    - Simple   : pipeline complet avec insight + historique multi-tour
    """
    sub_questions = detect_sub_questions(question)

    if sub_questions is None:
        result = await _run_sub_query(question, schema, pool, pharmacy_id, with_insight=True, rag_client=rag_client, semantic_catalog=semantic_catalog, schema_embeddings=schema_embeddings, conversation_history=conversation_history, language=language)
        return {
            "question": question,
            "is_compound": False,
            "sub_analyses": [result],
        }

    # Séquentiel — asyncio.gather sature Ollama et provoque des timeouts
    # Questions composées : historique non propagé (sous-questions prédéfinies, pas de contexte conversationnel)
    sub_analyses = []
    for q in sub_questions:
        try:
            result = await _run_sub_query(q, schema, pool, pharmacy_id, with_insight=False, rag_client=rag_client, semantic_catalog=semantic_catalog, schema_embeddings=schema_embeddings, language=language)
            sub_analyses.append(result)
        except Exception as e:
            sub_analyses.append({
                "question": q,
                "sql": "",
                "columns": [],
                "rows": [],
                "row_count": 0,
                "insight": f"Erreur lors de l'analyse : {e}",
            })

    return {
        "question": question,
        "is_compound": True,
        "sub_analyses": sub_analyses,
    }
