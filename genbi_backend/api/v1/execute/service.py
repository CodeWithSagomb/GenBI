import psycopg2
from core.sql_validator import validate_sql
from core.exceptions import DatabaseError
from core.pagination import PageParams


def execute_sql(sql: str, conn, page: PageParams) -> dict:
    """Valide puis exécute le SQL en lecture seule avec pagination.

    Enveloppe le SQL dans une sous-requête pour appliquer LIMIT/OFFSET sans
    conflit avec un éventuel LIMIT déjà présent dans la requête générée.
    """
    validate_sql(sql)

    paginated = (
        f"SELECT * FROM ({sql}) AS _q "
        f"LIMIT {page.limit} OFFSET {page.offset}"
    )

    try:
        with conn.cursor() as cur:
            cur.execute(paginated)
            columns = [desc[0] for desc in cur.description]
            rows = [list(row) for row in cur.fetchall()]
    except psycopg2.Error as e:
        raise DatabaseError(f"Erreur d'exécution SQL : {e}") from e

    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "limit": page.limit,
        "offset": page.offset,
    }
