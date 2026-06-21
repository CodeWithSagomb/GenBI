import re
from typing import Optional

_TEMPORAL_RE = re.compile(
    r"évolution|par mois|tendance|trend|monthly|mensuel|over.?time"
    r"|par semaine|weekly|par jour|daily|historique|history",
    re.IGNORECASE,
)

_SQL_LIMIT_RE = re.compile(r"\bLIMIT\s+\d+\b", re.IGNORECASE)

_TEMPORAL_COL_RE = re.compile(
    r"mois|month|date|year|année|semaine|week|jour|day",
    re.IGNORECASE,
)

_EXCLUDE_COL_RE = re.compile(r"_id$|_fcfa$", re.IGNORECASE)


def _is_numeric_nonneg(rows: list[list], col_idx: int) -> bool:
    """Toutes les valeurs de la colonne sont numériques et >= 0."""
    for row in rows:
        if col_idx >= len(row):
            return False
        v = row[col_idx]
        if v is None or not isinstance(v, (int, float)) or v < 0:
            return False
    return True


def _is_categorical(rows: list[list], col_idx: int) -> bool:
    """La colonne contient des valeurs textuelles (non numériques)."""
    for row in rows:
        if col_idx >= len(row):
            return False
        v = row[col_idx]
        if isinstance(v, (int, float)):
            return False
    return True


def detect_viz_hint(
    question: str,
    sql: str,
    columns: list[str],
    rows: list[list],
) -> Optional[str]:
    """Détermine structurellement le type de visualisation optimal.

    Règles par priorité :
    1. Signal temporel dans la question              → "line"
    2. LIMIT dans le SQL (top-N, données partielles) → "bar"
    3. Composition structurelle :
       2 cols + 2-4 lignes + col[0] catégorielle
       non temporelle + col[1] numérique ≥ 0         → "pie"
    4. Plus d'une ligne                              → "bar"
    5. Sinon                                         → None
    """
    if not rows or not columns or len(columns) < 2 or len(rows) <= 1:
        return None

    # 1. Signal temporel → line
    if _TEMPORAL_RE.search(question):
        return "line"

    # 2. LIMIT dans le SQL → top-N → bar
    if _SQL_LIMIT_RE.search(sql):
        return "bar"

    # 3. Composition structurelle → pie
    if (
        len(columns) == 2
        and 2 <= len(rows) <= 4
        and not _TEMPORAL_COL_RE.search(columns[0])
        and not _EXCLUDE_COL_RE.search(columns[0])
        and _is_categorical(rows, col_idx=0)
        and _is_numeric_nonneg(rows, col_idx=1)
    ):
        return "pie"

    # 4. Comparaison / classement → bar
    return "bar"
