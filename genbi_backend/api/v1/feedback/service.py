import psycopg2
from fastapi import Request
from core.exceptions import DatabaseError
from core.rag import index_example
from api.v1.feedback.schemas import FeedbackRequest


def insert_feedback(body: FeedbackRequest, pharmacy_id: int, conn, request: Request) -> dict:
    """Insère un feedback via genbi_write.

    Si rating == 'good' et sql_generated non vide, indexe la paire
    Question→SQL dans ChromaDB (best-effort — n'impacte pas la réponse HTTP).
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO raw.feedback
                    (pharmacy_id, question, sql_generated, rating, comment)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING feedback_id, pharmacy_id, created_at
                """,
                (
                    pharmacy_id,
                    body.question,
                    body.sql_generated,
                    body.rating,
                    body.comment,
                ),
            )
            row = cur.fetchone()
        conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        raise DatabaseError(f"Erreur lors de l'enregistrement du feedback : {e}") from e

    if body.rating == "good" and body.sql_generated:
        rag_client = getattr(request.app.state, "rag_client", None)
        if rag_client is not None:
            index_example(rag_client, pharmacy_id, body.question, body.sql_generated)

    return {
        "feedback_id": row[0],
        "pharmacy_id": row[1],
        "created_at": row[2].isoformat(),
    }
