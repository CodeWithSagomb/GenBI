"""Validation sémantique du résultat SQL par rapport à la question.

Vérifie que la cardinalité du résultat est cohérente avec l'intention
de la question. Si incohérente, retourne un hint de correction pour
déclencher une re-génération SQL ciblée.

Conservateur : préfère les faux négatifs (laisser passer) aux faux
positifs (re-générer inutilement). Seuls les cas clairement suspects
sont signalés.
"""
import re
from typing import Optional


_EMPTY_OK_KW = ("y a-t-il", "existe", "est-ce qu", "are there", "is there", "avons-nous", "do we have")
_SCALAR_KW   = ("quel est le total", "quel est la", "quel montant total", "what is the total", "what is the", "how many")
_GROUP_KW    = ("par ", "by ", "chaque", "each", "répartition", "breakdown", "liste", "list")


def check_result_coherence(
    question: str,
    columns: list,
    rows: list,
) -> Optional[str]:
    """Retourne un hint de correction si le résultat est incohérent, None sinon.

    None  → résultat vraisemblable, rien à faire.
    str   → problème détecté, la string est un RAPPEL à injecter dans
            le prochain appel generate_sql() pour corriger le SQL.
    """
    q    = question.lower()
    n    = len(rows)
    ncol = len(columns)

    # 1. Zéro lignes — suspect sauf questions existence / bool
    if n == 0 and not any(kw in q for kw in _EMPTY_OK_KW):
        return (
            "RAPPEL RÉSULTAT VIDE : la requête précédente a retourné 0 lignes. "
            "Vérifie que les JOIN, les noms de colonnes et les filtres de date sont corrects. "
            "N'ajoute PAS de filtre sur une période spécifique sauf si la question le demande explicitement."
        )

    # 2. Question scalaire (1 valeur globale) sans groupement → >3 lignes suspect
    is_scalar  = any(kw in q for kw in _SCALAR_KW)
    has_group  = any(kw in q for kw in _GROUP_KW)
    if is_scalar and not has_group and ncol == 1 and n > 3:
        return (
            f"RAPPEL SCALAIRE : la question attend une valeur unique (agrégat global) "
            f"mais {n} lignes ont été retournées. "
            "Utilise SUM() ou COUNT() global sans GROUP BY."
        )

    # 3. "top N" → attend N lignes maximum
    m = re.search(r"\btop\s+(\d+)\b", q)
    if m:
        expected = int(m.group(1))
        if n == 0:
            return (
                f"RAPPEL TOP {expected} : la question demande le top {expected} "
                "mais 0 lignes ont été retournées. Vérifie le ORDER BY et les filtres."
            )
        if n > expected * 2:
            return (
                f"RAPPEL TOP {expected} : {n} lignes retournées alors que le top {expected} "
                f"est demandé. Ajoute LIMIT {expected} et ORDER BY … DESC."
            )

    return None
