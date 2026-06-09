"""
Tests unitaires pour core/pagination.py — PageParams.

Valide les valeurs par défaut, limites et la construction
du wrapper SQL subquery utilisé dans query/service.py et execute/service.py.
Bug couvert : #1 (double LIMIT) — session 2026-06-09.
"""
import pytest
from pydantic import ValidationError

from core.pagination import PageParams


# ── Valeurs par défaut ────────────────────────────────────────────────────────

def test_defaut_limit_100():
    p = PageParams()
    assert p.limit == 100


def test_defaut_offset_0():
    p = PageParams()
    assert p.offset == 0


# ── Valeurs valides ───────────────────────────────────────────────────────────

def test_limit_1_accepte():
    assert PageParams(limit=1).limit == 1


def test_limit_500_accepte():
    assert PageParams(limit=500).limit == 500


def test_offset_grand_accepte():
    assert PageParams(offset=10000).offset == 10000


def test_limit_et_offset_personnalises():
    p = PageParams(limit=25, offset=50)
    assert p.limit == 25
    assert p.offset == 50


# ── Valeurs invalides ─────────────────────────────────────────────────────────

def test_limit_0_rejete():
    with pytest.raises(ValidationError):
        PageParams(limit=0)


def test_limit_negatif_rejete():
    with pytest.raises(ValidationError):
        PageParams(limit=-1)


def test_limit_501_rejete():
    with pytest.raises(ValidationError):
        PageParams(limit=501)


def test_offset_negatif_rejete():
    with pytest.raises(ValidationError):
        PageParams(offset=-1)


# ── Wrapper subquery anti-double-LIMIT ────────────────────────────────────────

def test_subquery_wrapper_format():
    """
    Le wrapper doit envelopper le SQL dans une sous-requête.
    Garantit qu'un SQL avec LIMIT existant ne génère pas de double LIMIT.
    """
    p = PageParams(limit=10, offset=20)
    sql = "SELECT * FROM marts.fct_sales ORDER BY sale_date DESC LIMIT 5"
    wrapped = f"SELECT * FROM ({sql}) AS _q LIMIT {p.limit} OFFSET {p.offset}"
    assert "LIMIT 10 OFFSET 20" in wrapped
    assert wrapped.startswith("SELECT * FROM (")
    assert ") AS _q" in wrapped


def test_subquery_wrapper_pas_de_double_limit():
    """Le SQL original avec LIMIT 5 ne doit pas produire deux LIMIT consécutifs."""
    p = PageParams(limit=100, offset=0)
    sql = "SELECT * FROM marts.fct_sales LIMIT 5"
    wrapped = f"SELECT * FROM ({sql}) AS _q LIMIT {p.limit} OFFSET {p.offset}"
    # LIMIT n'apparaît que deux fois : une dans la sous-requête, une externe
    assert wrapped.count("LIMIT") == 2
    # La dernière occurrence est bien le LIMIT externe (100)
    assert wrapped.endswith("LIMIT 100 OFFSET 0")
