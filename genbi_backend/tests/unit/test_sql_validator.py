"""
TDD — sql_validator.py
Tests écrits AVANT l'implémentation.
Tous doivent ÉCHOUER au premier run (module absent).
"""
import pytest
from core.exceptions import SQLValidationError


def validate(sql: str):
    """Raccourci d'import pour chaque test."""
    from core.sql_validator import validate_sql
    return validate_sql(sql)


# ── Cas autorisés ────────────────────────────────────────────────────────────

def test_select_simple_accepte():
    validate("SELECT * FROM marts.fct_sales")


def test_select_with_join_accepte():
    validate(
        "SELECT s.sale_id, p.commercial_name "
        "FROM marts.fct_sales s "
        "JOIN marts.dim_products p ON s.sale_id = p.product_id"
    )


def test_select_with_subquery_accepte():
    validate(
        "SELECT * FROM (SELECT sale_id FROM marts.fct_sales WHERE total_amount_fcfa > 1000) sub"
    )


def test_select_marts_schema_accepte():
    validate("SELECT SUM(total_amount_fcfa) FROM marts.fct_sales WHERE sale_month = 5")


# ── Cas refusés — sécurité critique ──────────────────────────────────────────

def test_delete_rejete():
    with pytest.raises(SQLValidationError):
        validate("DELETE FROM marts.fct_sales")


def test_drop_table_rejete():
    with pytest.raises(SQLValidationError):
        validate("DROP TABLE marts.fct_sales")


def test_insert_rejete():
    with pytest.raises(SQLValidationError):
        validate("INSERT INTO marts.fct_sales VALUES (1, 2, 3)")


def test_update_rejete():
    with pytest.raises(SQLValidationError):
        validate("UPDATE marts.fct_sales SET total_amount_fcfa = 0")


def test_truncate_rejete():
    with pytest.raises(SQLValidationError):
        validate("TRUNCATE TABLE marts.fct_sales")


def test_create_table_rejete():
    with pytest.raises(SQLValidationError):
        validate("CREATE TABLE hack AS SELECT * FROM marts.fct_sales")


# ── Cas limites ───────────────────────────────────────────────────────────────

def test_sql_vide_rejete():
    with pytest.raises(SQLValidationError):
        validate("")


def test_injection_semicolon_double_statement_rejete():
    with pytest.raises(SQLValidationError):
        validate("SELECT 1; DROP TABLE marts.fct_sales")


def test_select_suivi_de_drop_rejete():
    with pytest.raises(SQLValidationError):
        validate("SELECT * FROM marts.fct_sales; DELETE FROM marts.fct_sales")
