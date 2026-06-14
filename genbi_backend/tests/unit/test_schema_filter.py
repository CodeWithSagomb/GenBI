"""Tests unitaires — core/schema_filter.py (Phase 3)."""
from unittest.mock import patch

from core.schema_filter import (
    parse_schema_to_records,
    filter_schema_for_question,
    _lexical_score,
    _cosine,
)

SCHEMA = """\
marts.fct_sales: sale_id, sale_month, total_amount_fcfa, payment_method
marts.dim_products: product_id, commercial_name, product_category, is_generic
marts.dim_clients: client_id, client_name, client_type, is_chronic
staging.stg_raw__sale_details: sale_detail_id, sale_id, product_id, quantity
marts.fct_purchases: purchase_id, product_id, wholesaler_name, quantity_ordered
marts.fct_missed_sales: missed_id, missed_month, missed_year
marts.dim_stocks: product_id, quantity_in_stock, safety_stock_threshold\
"""

# Vecteur fictif 4-D pour les tests (nomic-embed-text est 768-D en réel)
FAKE_VEC = [1.0, 0.0, 0.0, 0.0]

FAKE_EMBEDDINGS = {
    "marts.fct_sales":               [1.0, 0.0, 0.0, 0.0],
    "marts.dim_products":            [0.0, 1.0, 0.0, 0.0],
    "marts.dim_clients":             [0.0, 0.0, 1.0, 0.0],
    "staging.stg_raw__sale_details": [0.5, 0.5, 0.0, 0.0],
    "marts.fct_purchases":           [0.0, 0.0, 0.0, 1.0],
    "marts.fct_missed_sales":        [0.3, 0.0, 0.0, 0.7],
    "marts.dim_stocks":              [0.0, 0.1, 0.0, 0.9],
}


# ── parse_schema_to_records ────────────────────────────────────────────────────

def test_parse_retourne_bonne_longueur():
    records = parse_schema_to_records(SCHEMA)
    assert len(records) == 7


def test_parse_extrait_table_et_columns():
    records = parse_schema_to_records(SCHEMA)
    first = records[0]
    assert first["table"] == "marts.fct_sales"
    assert "sale_id" in first["columns"]
    assert first["line"].startswith("marts.fct_sales")


# ── _cosine ────────────────────────────────────────────────────────────────────

def test_cosine_vecteurs_identiques_retourne_1():
    v = [1.0, 2.0, 3.0]
    assert abs(_cosine(v, v) - 1.0) < 1e-9


def test_cosine_vecteurs_orthogonaux_retourne_0():
    assert _cosine([1.0, 0.0], [0.0, 1.0]) == 0.0


# ── _lexical_score ────────────────────────────────────────────────────────────

def test_lexical_score_match_exact():
    score = _lexical_score({"sales", "total"}, "marts.fct_sales", "total_amount_fcfa")
    assert score > 0


def test_lexical_score_aucun_match():
    score = _lexical_score({"xyz", "abc"}, "marts.fct_sales", "sale_id, total_amount_fcfa")
    assert score == 0.0


# ── filter_schema_for_question ────────────────────────────────────────────────

def test_filter_fallback_si_embeddings_none():
    result = filter_schema_for_question(SCHEMA, "Quel est mon CA ?", schema_embeddings=None)
    assert result == SCHEMA


def test_filter_fallback_si_embed_leve_exception():
    with patch("core.schema_filter._embed", side_effect=RuntimeError("ollama down")):
        result = filter_schema_for_question(SCHEMA, "Quel est mon CA ?", FAKE_EMBEDDINGS)
    assert result == SCHEMA


def test_tables_core_toujours_presentes():
    """Quelle que soit la question, les 3 tables core doivent apparaître."""
    with patch("core.schema_filter._embed", return_value=FAKE_VEC):
        result = filter_schema_for_question(SCHEMA, "question quelconque", FAKE_EMBEDDINGS, top_k=3)
    assert "marts.fct_sales" in result
    assert "marts.dim_products" in result
    assert "staging.stg_raw__sale_details" in result


def test_filter_retourne_tables_pertinentes():
    """Question sur les ventes → marts.fct_sales présent dans le résultat."""
    q_vec = [1.0, 0.0, 0.0, 0.0]  # proche de fct_sales
    with patch("core.schema_filter._embed", return_value=q_vec):
        result = filter_schema_for_question(SCHEMA, "combien de ventes ce mois ?", FAKE_EMBEDDINGS, top_k=4)
    assert "marts.fct_sales" in result


def test_filter_respecte_top_k():
    with patch("core.schema_filter._embed", return_value=FAKE_VEC):
        result = filter_schema_for_question(SCHEMA, "question", FAKE_EMBEDDINGS, top_k=4)
    lines = [l for l in result.strip().split("\n") if l]
    assert len(lines) == 4
