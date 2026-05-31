"""Classifie les colonnes SQL par type sémantique.

Utilisé par le générateur d'insight pour éviter que le LLM confonde
un COUNT avec un montant FCFA. Ajouter ici les nouveaux types de colonnes
(ex: score RAG, distance embedding) au fur et à mesure des phases.
"""

_FINANCIAL = frozenset({"amount", "ca", "revenue", "montant", "fcfa", "price", "prix"})
_COUNT = frozenset({"count", "total_sales", "nombre", "nb", "sales", "nb_ventes"})
_QUANTITY = frozenset({"quantity", "quantite", "qty", "total_quantity"})


def classify_column(col: str) -> str:
    """Retourne le type sémantique d'une colonne à partir de son nom.

    Retourne : "financial" | "count" | "quantity" | "unknown"
    """
    col_lower = col.lower()
    if any(kw in col_lower for kw in _FINANCIAL):
        return "financial"
    if any(kw in col_lower for kw in _COUNT):
        return "count"
    if any(kw in col_lower for kw in _QUANTITY):
        return "quantity"
    return "unknown"


_LABELS = {
    "financial": "MONTANT FINANCIER en FCFA",
    "count":     "NOMBRE DE TRANSACTIONS (pas un montant FCFA)",
    "quantity":  "NOMBRE D'UNITÉS VENDUES (pas un montant FCFA)",
    "unknown":   "donnée",
}


def annotate_column_types(columns: list) -> str:
    """Génère une annotation lisible par le LLM pour chaque colonne.

    Exemple de sortie :
        total_sales: NOMBRE DE TRANSACTIONS (pas un montant FCFA)
        total_amount_fcfa: MONTANT FINANCIER en FCFA
    """
    return "\n".join(
        f"  {col}: {_LABELS[classify_column(col)]}"
        for col in columns
    )
