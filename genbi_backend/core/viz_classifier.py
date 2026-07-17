import re
from typing import Optional

from core.rules_loader import rules

# _SQL_LIMIT_RE est une règle structurelle SQL (pas une règle métier) — reste hardcodé.
_SQL_LIMIT_RE = re.compile(r"\bLIMIT\s+\d+\b", re.IGNORECASE)


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
    """La colonne contient des valeurs textuelles ou booléennes (non numériques).

    bool est une sous-classe de int en Python — on l'exclut explicitement pour
    que True/False (is_generic) soient traités comme des catégories, pas des nombres.
    """
    for row in rows:
        if col_idx >= len(row):
            return False
        v = row[col_idx]
        if not isinstance(v, bool) and isinstance(v, (int, float)):
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
    3. Signal de ranking (most/best/highest/…)       → "bar"
    4. Composition structurelle :
       2 cols + 2-4 lignes + col[0] catégorielle
       non temporelle + col[1] numérique ≥ 0         → "pie"
    5. Plus d'une ligne                              → "bar"
    6. Sinon                                         → None
    """
    if not rows or not columns or len(columns) < 2 or len(rows) <= 1:
        return None

    # 1. Signal temporel → line
    if rules.temporal_re.search(question):
        return "line"

    # 2. LIMIT dans le SQL → top-N → bar
    if _SQL_LIMIT_RE.search(sql):
        return "bar"

    # 3. Signal de ranking → comparaison, pas composition → bar
    if rules.ranking_re.search(question):
        return "bar"

    # 4. Composition structurelle → pie
    _is_comp_q = bool(rules.composition_re.search(question))
    _thr = rules.viz["thresholds"]
    _max_rows = _thr["pie_max_rows_composition"] if _is_comp_q else _thr["pie_max_rows_strict"]
    _col0_ok = (
        not rules.temporal_col_re.search(columns[0])
        and not rules.exclude_col_re.search(columns[0])
        and _is_categorical(rows, col_idx=0)
    )
    if (
        2 <= len(rows) <= _max_rows
        and len(columns) >= 2
        and _col0_ok
        and _is_numeric_nonneg(rows, col_idx=1)
        and (len(columns) == 2 or _is_comp_q)
    ):
        return "pie"

    # 4. Comparaison / classement → bar
    return "bar"
