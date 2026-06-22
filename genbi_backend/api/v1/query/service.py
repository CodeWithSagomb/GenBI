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
from core.viz_classifier import detect_viz_hint
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

_DOW_FR = {0: "Dimanche", 1: "Lundi", 2: "Mardi", 3: "Mercredi", 4: "Jeudi", 5: "Vendredi", 6: "Samedi"}
_DOW_EN = {0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday"}
_DOW_COLS = {"sale_dow", "dow", "day_of_week"}

# Booléens métier → libellés lisibles (évite "True/False" dans les insights)
_BOOL_LABELS: dict[str, dict] = {
    "is_generic":               {True: "Génériques",  False: "Princeps"},
    "is_anonymous":             {True: "Anonyme",     False: "Identifié"},
    "is_chronic":               {True: "Chronique",   False: "Ponctuel"},
    "is_below_safety_threshold":{True: "Sous seuil",  False: "Stock OK"},
}


def _serialize_val(v):
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v


def _serialize_row(row):
    return [_serialize_val(v) for v in row]


def _humanize_booleans(columns: list[str], rows: list[list]) -> list[list]:
    """Convertit les colonnes booléennes connues en libellés lisibles."""
    bool_indices = [(i, _BOOL_LABELS[col]) for i, col in enumerate(columns) if col in _BOOL_LABELS]
    if not bool_indices:
        return rows
    result = []
    for row in rows:
        new_row = list(row)
        for idx, label_map in bool_indices:
            if idx < len(new_row):
                new_row[idx] = label_map.get(new_row[idx], new_row[idx])
        result.append(new_row)
    return result


def _humanize_dow(columns: list[str], rows: list[list], language: str = 'fr') -> list[list]:
    """Convertit les entiers sale_dow (0=Dim … 6=Sam) en noms de jours."""
    dow_map = _DOW_EN if language == 'en' else _DOW_FR
    dow_indices = [i for i, c in enumerate(columns) if c in _DOW_COLS]
    if not dow_indices:
        return rows
    return [
        [dow_map.get(int(v), v) if i in dow_indices and isinstance(v, (int, float)) else v
         for i, v in enumerate(row)]
        for row in rows
    ]


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
    rows = _humanize_dow(columns, rows, language)
    rows = _humanize_booleans(columns, rows)
    results = {"columns": columns, "rows": rows}
    if with_insight and rows:
        insight = await generate_insight(question, results, language=language)
    elif with_insight and not rows:
        insight = "Aucune donnée disponible pour cette période ou cette sélection." if language == 'fr' else "No data available for this period or selection."
    else:
        insight = ""

    viz_hint = detect_viz_hint(question, sql, columns, rows)

    return {
        "question": question,
        "sql": sql,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "limit": page.limit,
        "offset": page.offset,
        "insight": insight,
        "viz_hint": viz_hint,
    }
