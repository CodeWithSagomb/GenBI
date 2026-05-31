import psycopg2
from core.exceptions import DatabaseError
from api.v1.feedback.schemas import FeedbackRequest


def insert_feedback(body: FeedbackRequest, pharmacy_id: int, conn) -> dict:
    """Insère un feedback via genbi_write et retourne l'id + timestamp."""
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

    return {
        "feedback_id": row[0],
        "pharmacy_id": row[1],
        "created_at": row[2].isoformat(),
    }
