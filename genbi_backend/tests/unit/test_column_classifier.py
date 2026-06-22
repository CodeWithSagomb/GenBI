"""Tests unitaires — core/column_classifier.py."""

from core.column_classifier import classify_column, annotate_column_types


# ── classify_column ───────────────────────────────────────────────────────────

def test_classifie_montant_financier():
    assert classify_column("total_amount_fcfa") == "financial"
    assert classify_column("ca_total") == "financial"


def test_classifie_comptage():
    assert classify_column("nb_ventes") == "count"
    assert classify_column("nombre_ventes") == "count"
    assert classify_column("count_transactions") == "count"
    assert classify_column("total_ventes") == "count"   # COUNT(*) AS total_ventes → jamais FCFA
    assert classify_column("panier_moyen") == "count"   # AVG(nb_products_in_cart) → jamais FCFA


def test_classifie_sales_comme_financier():
    # "sales" et "total_sales" → MONTANT FINANCIER (SUM de FCFA)
    # avant fix : "sales" était dans _COUNT → monthly_sales → faux type TRANSACTIONS
    assert classify_column("total_sales") == "financial"
    assert classify_column("monthly_sales") == "financial"


def test_classifie_quantite():
    assert classify_column("total_quantity_sold") == "quantity"
    assert classify_column("qty_dispensed") == "quantity"


def test_classifie_inconnu():
    assert classify_column("commercial_name") == "unknown"
    assert classify_column("product_id") == "unknown"


# ── annotate_column_types ─────────────────────────────────────────────────────

def test_annotation_count_pas_fcfa():
    result = annotate_column_types(["nb_ventes"])
    assert "NOMBRE DE TRANSACTIONS" in result
    assert "pas un montant fcfa" in result.lower()


def test_annotation_financial_fcfa():
    result = annotate_column_types(["total_amount_fcfa"])
    assert "MONTANT FINANCIER" in result


def test_annotation_quantity_unites():
    result = annotate_column_types(["total_quantity_sold"])
    assert "UNITÉS" in result


def test_annotation_inconnu_donnee():
    result = annotate_column_types(["commercial_name"])
    assert "donnée" in result


def test_annotation_plusieurs_colonnes():
    result = annotate_column_types(["nb_ventes", "total_amount_fcfa"])
    assert "NOMBRE DE TRANSACTIONS" in result
    assert "MONTANT FINANCIER" in result
