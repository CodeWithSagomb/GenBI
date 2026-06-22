import re
from typing import Optional

_TEMPORAL_RE = re.compile(
    r"évolution|évolue|par mois|tendance|trend|monthly|mensuel|over.?time"
    r"|par semaine|weekly|par jour(?!\s+de\s+la)|daily|historique|history",
    re.IGNORECASE,
)

_SQL_LIMIT_RE = re.compile(r"\bLIMIT\s+\d+\b", re.IGNORECASE)

_TEMPORAL_COL_RE = re.compile(
    r"mois|month|date|year|année|semaine|week|jour|day",
    re.IGNORECASE,
)

_EXCLUDE_COL_RE = re.compile(r"_id$|_fcfa$", re.IGNORECASE)

_COMPOSITION_RE = re.compile(
    r"répartition|distribution|part\s+d[eu']|breakdown|share"
    r"|composition|proportion"
    r"|par\s+(mode|type|catég|categ|origin|assur|payment|insurance)",
    re.IGNORECASE,
)

_RANKING_RE = re.compile(
    r"\bmost\b|\bbest\b|\bhighest\b|\blargest\b|\bbiggest\b"
    r"|\bleading\b|\blowest\b|\bworst\b|\bfewest\b"
    r"|\ble\s+plus\b|\bmeilleur\b|\bpire\b",
    re.IGNORECASE,
)


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
    if _TEMPORAL_RE.search(question):
        return "line"

    # 2. LIMIT dans le SQL → top-N → bar
    if _SQL_LIMIT_RE.search(sql):
        return "bar"

    # 3. Signal de ranking → comparaison, pas composition → bar
    if _RANKING_RE.search(question):
        return "bar"

    # 4. Composition structurelle → pie
    # _COMPOSITION_RE (répartition/distribution/breakdown/…) :
    #   - relaxe la contrainte "2 colonnes exactement" (LLM génère parfois 3)
    #   - étend la limite de lignes à 5 (5 catégories = encore lisible en pie)
    # Sans mot de composition : 2 colonnes + max 4 lignes (règle structurelle stricte).
    _is_comp_q = bool(_COMPOSITION_RE.search(question))
    _max_rows = 5 if _is_comp_q else 4
    _col0_ok = (
        not _TEMPORAL_COL_RE.search(columns[0])
        and not _EXCLUDE_COL_RE.search(columns[0])
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
