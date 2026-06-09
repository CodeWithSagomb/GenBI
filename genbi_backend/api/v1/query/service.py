from datetime import date, datetime
from decimal import Decimal

from core.llm import generate_sql, generate_insight
from core.sql_validator import validate_sql
from core.exceptions import DatabaseError
from core.pagination import PageParams

import psycopg2


def _serialize_val(v):
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v


def _serialize_row(row):
    return [_serialize_val(v) for v in row]


async def query_pipeline(
    question: str,
    schema: str,
    conn,
    page: PageParams,
) -> dict:
    """Pipeline complet : question → SQL → exécution → insight."""
    sql = await generate_sql(schema, question)
    validate_sql(sql)

    paginated = f"SELECT * FROM ({sql}) AS _q LIMIT {page.limit} OFFSET {page.offset}"
    try:
        with conn.cursor() as cur:
            cur.execute(paginated)
            columns = [desc[0] for desc in cur.description]
            rows = [_serialize_row(row) for row in cur.fetchall()]
    except psycopg2.Error as e:
        raise DatabaseError(f"Erreur d'exécution SQL : {e}") from e

    results = {"columns": columns, "rows": rows}
    insight = await generate_insight(question, results)

    return {
        "question": question,
        "sql": sql,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "limit": page.limit,
        "offset": page.offset,
        "insight": insight,
    }
