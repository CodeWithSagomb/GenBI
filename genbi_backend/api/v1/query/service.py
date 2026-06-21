import logging
from datetime import date, datetime
from decimal import Decimal

from config import settings

logger = logging.getLogger(__name__)
from core.llm import generate_sql, generate_insight, repair_sql
from core.rag import retrieve_examples
from core.schema_filter import filter_schema_for_question
from core.semantic_layer import resolve_semantics
from core.sql_validator import validate_sql
from core.exceptions import DatabaseError
from core.pagination import PageParams

import psycopg2

_MOIS_FR = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
}
_MOIS_EN = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
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


def _humanize_months(columns: list[str], rows: list[list], language: str = 'fr') -> list[list]:
    """Convertit les numéros de mois ISO en noms (français ou anglais) pour les colonnes mois."""
    month_map = _MOIS_EN if language == 'en' else _MOIS_FR
    month_indices = [i for i, c in enumerate(columns) if c in _MONTH_COLS]
    if not month_indices:
        return rows
    return [
        [month_map.get(v, v) if i in month_indices else v for i, v in enumerate(row)]
        for row in rows
    ]


async def query_pipeline(
    question: str,
    schema: str,
    conn,
    page: PageParams,
    with_insight: bool = True,
    rag_client=None,
    pharmacy_id: int | None = None,
    semantic_catalog: dict | None = None,
    schema_embeddings: dict | None = None,
    conversation_history: list | None = None,
    language: str = 'fr',
) -> dict:
    """Pipeline complet : question → SQL → exécution → insight (optionnel).

    - rag_client + pharmacy_id  : exemples ChromaDB injectés dans le prompt
    - semantic_catalog          : termes métier détectés → bloc <semantic_context>
    - conversation_history      : turns précédents pour le chat multi-tour (Phase 4)
    """
    examples: list = []
    if rag_client is not None and pharmacy_id is not None:
        examples = retrieve_examples(rag_client, pharmacy_id, question, n=3)

    semantic_context = resolve_semantics(question, semantic_catalog)
    filtered_schema = filter_schema_for_question(schema, question, schema_embeddings)

    sql = await generate_sql(filtered_schema, question, examples or None, semantic_context, conversation_history)
    validate_sql(sql)

    paginated = f"SELECT * FROM ({sql}) AS _q LIMIT {page.limit} OFFSET {page.offset}"
    columns: list = []
    rows: list = []
    last_error: psycopg2.Error | None = None
    for attempt in range(settings.SQL_MAX_REPAIR_ATTEMPTS + 1):
        try:
            with conn.cursor() as cur:
                cur.execute(paginated)
                columns = [desc[0] for desc in cur.description]
                rows = [_serialize_row(row) for row in cur.fetchall()]
            last_error = None
            break
        except psycopg2.Error as e:
            last_error = e
            conn.rollback()
            if attempt < settings.SQL_MAX_REPAIR_ATTEMPTS:
                logger.warning(
                    "[SQL-REPAIR] tentative %d/%d — erreur: %s",
                    attempt + 1, settings.SQL_MAX_REPAIR_ATTEMPTS, str(e).split("\n")[0],
                )
                sql = await repair_sql(schema, question, sql, str(e))
                logger.info("[SQL-REPAIR] SQL réparé: %s", sql[:120])
                validate_sql(sql)
                paginated = f"SELECT * FROM ({sql}) AS _q LIMIT {page.limit} OFFSET {page.offset}"
    if last_error is not None:
        raise DatabaseError(f"Erreur d'exécution SQL : {last_error}") from last_error

    rows = _humanize_months(columns, rows, language)
    results = {"columns": columns, "rows": rows}
    if with_insight and rows:
        insight = await generate_insight(question, results, language=language)
    elif with_insight and not rows:
        insight = "Aucune donnée disponible pour cette période ou cette sélection." if language == 'fr' else "No data available for this period or selection."
    else:
        insight = ""

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
