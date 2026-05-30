import psycopg2
from psycopg2 import pool
from fastapi import Depends, Request

from config import settings
from core.auth import get_current_pharmacy
from core.exceptions import DatabaseError


def create_pool() -> pool.ThreadedConnectionPool:
    return pool.ThreadedConnectionPool(
        minconn=2,
        maxconn=10,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_READONLY_USER,
        password=settings.DB_READONLY_PASSWORD,
    )


def get_db_conn(
    request: Request,
    pharmacy_id: int = Depends(get_current_pharmacy),
):
    """Dependency : connexion readonly avec RLS actif pour la pharmacie courante."""
    conn = request.app.state.db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SET app.current_pharmacy_id = %s", (pharmacy_id,))
        conn.commit()
        yield conn
    except psycopg2.Error as e:
        conn.rollback()
        raise DatabaseError(f"Erreur base de données : {e}") from e
    finally:
        try:
            with conn.cursor() as cur:
                cur.execute("RESET app.current_pharmacy_id")
            conn.commit()
        except Exception:
            pass
        request.app.state.db_pool.putconn(conn)
