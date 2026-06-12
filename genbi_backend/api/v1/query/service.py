from datetime import date, datetime
from decimal import Decimal

from core.llm import generate_sql, generate_insight
from core.sql_validator import validate_sql
from core.exceptions import DatabaseError
from core.pagination import PageParams

import psycopg2

_MOIS_FR = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
}
_MONTH_COLS = {"mois", "sale_month", "missed_month"}


def _serialize_val(v):
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v


def _serialize_row(row):
    return [_serialize_val(v) for v in row]


def _humanize_months(columns: list[str], rows: list[list]) -> list[list]:
    """Convertit les numéros de mois ISO en noms français pour les colonnes mois."""
    month_indices = [i for i, c in enumerate(columns) if c in _MONTH_COLS]
    if not month_indices:
        return rows
    return [
        [_MOIS_FR.get(v, v) if i in month_indices else v for i, v in enumerate(row)]
        for row in rows
    ]


async def query_pipeline(
    question: str,
    schema: str,
    conn,
    page: PageParams,
    with_insight: bool = True,
) -> dict:
    """Pipeline complet : question → SQL → exécution → insight (optionnel)."""
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

    rows = _humanize_months(columns, rows)
    results = {"columns": columns, "rows": rows}
    insight = await generate_insight(question, results) if with_insight else ""

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
