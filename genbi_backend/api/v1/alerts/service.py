import logging
from datetime import date, datetime
from decimal import Decimal

import psycopg2

from core.llm import generate_insight
from core.exceptions import DatabaseError

logger = logging.getLogger(__name__)

_ALERT_QUERIES = [
    {
        "id": "stock_critique",
        "severity": "danger",
        "title": "Stocks sous seuil de sécurité",
        "question": "Quels produits sont sous le seuil de sécurité de stock ?",
        "sql": """
            SELECT commercial_name AS produit,
                   quantity_in_stock AS stock_actuel,
                   safety_stock_threshold AS seuil
            FROM marts.dim_stocks
            WHERE is_below_safety_threshold = TRUE
            ORDER BY quantity_in_stock ASC
        """,
    },
    {
        "id": "lots_expirants",
        "severity": "warning",
        "title": "Lots expirant dans 30 jours",
        "question": "Quels lots de médicaments expirent dans les 30 prochains jours ?",
        "sql": """
            SELECT commercial_name AS produit,
                   batch_number AS lot,
                   expiration_date AS expiration,
                   days_until_expiry AS jours_restants
            FROM marts.dim_stocks
            WHERE days_until_expiry >= 0 AND days_until_expiry <= 30
            ORDER BY days_until_expiry ASC
        """,
    },
    {
        "id": "taux_service",
        "severity": "info",
        "title": "Taux de service fournisseurs",
        "question": "Quel est le taux de service de chaque fournisseur grossiste ?",
        "sql": """
            SELECT wholesaler_name AS fournisseur,
                   ROUND(100.0 * SUM(quantity_received)
                         / NULLIF(SUM(quantity_ordered), 0), 1) AS taux_service_pct
            FROM marts.fct_purchases
            GROUP BY wholesaler_name
            ORDER BY taux_service_pct ASC
        """,
    },
]


def _serialize(v):
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v


async def generate_alerts(conn) -> list[dict]:
    """Exécute les 3 requêtes prédéfinies et génère un insight LLM si rows > 0."""
    results = []
    for q in _ALERT_QUERIES:
        try:
            with conn.cursor() as cur:
                cur.execute(q["sql"])
                columns = [desc[0] for desc in cur.description]
                rows = [[_serialize(v) for v in row] for row in cur.fetchall()]
        except psycopg2.Error as e:
            raise DatabaseError(f"Erreur alerte {q['id']} : {e}") from e

        row_count = len(rows)
        insight = ""
        if row_count > 0:
            try:
                insight = await generate_insight(
                    q["question"], {"columns": columns, "rows": rows}
                )
            except Exception as exc:
                logger.warning("[ALERTS] insight échoué pour %s : %s", q["id"], exc)

        results.append({
            "id": q["id"],
            "severity": q["severity"],
            "title": q["title"],
            "columns": columns,
            "rows": rows,
            "row_count": row_count,
            "insight": insight,
        })

    return results
