"""
Tests unitaires pour _serialize_val / _serialize_row.

Ces fonctions convertissent les types psycopg2 non-JSON-sérialisables
(Decimal, date, datetime) avant de renvoyer les données au frontend.
Bugs couverts ici : #4 (Decimal) et #5 (date) — session 2026-06-09.
"""
from datetime import date, datetime
from decimal import Decimal

import pytest

from api.v1.query.service import _serialize_val, _serialize_row
from api.v1.execute.service import _serialize_val as _serialize_val_exec


# ── _serialize_val : types psycopg2 ──────────────────────────────────────────

def test_decimal_converti_en_float():
    assert _serialize_val(Decimal("12345.67")) == pytest.approx(12345.67)
    assert isinstance(_serialize_val(Decimal("0")), float)


def test_decimal_grand_nombre():
    assert _serialize_val(Decimal("16364700.00")) == pytest.approx(16364700.0)


def test_date_converti_en_isoformat():
    d = date(2026, 6, 30)
    assert _serialize_val(d) == "2026-06-30"


def test_datetime_converti_en_isoformat():
    dt = datetime(2026, 3, 15, 10, 30, 0)
    assert _serialize_val(dt) == "2026-03-15T10:30:00"


def test_int_passe_tel_quel():
    assert _serialize_val(42) == 42


def test_str_passe_tel_quel():
    assert _serialize_val("Pharmacie Bourguiba") == "Pharmacie Bourguiba"


def test_none_passe_tel_quel():
    assert _serialize_val(None) is None


def test_float_passe_tel_quel():
    assert _serialize_val(3.14) == pytest.approx(3.14)


def test_bool_passe_tel_quel():
    assert _serialize_val(True) is True
    assert _serialize_val(False) is False


# ── _serialize_row : ligne complète ──────────────────────────────────────────

def test_serialize_row_mixte():
    row = (1, Decimal("500.50"), date(2026, 4, 1), "Glucophage", None)
    result = _serialize_row(row)
    assert result == [1, pytest.approx(500.50), "2026-04-01", "Glucophage", None]


def test_serialize_row_vide():
    assert _serialize_row(()) == []


def test_serialize_row_tout_int():
    assert _serialize_row((1, 2, 3)) == [1, 2, 3]


# ── Cohérence query/service == execute/service ────────────────────────────────

def test_serialize_identique_dans_les_deux_services():
    """Les deux services doivent produire exactement le même résultat."""
    val = Decimal("9999.99")
    assert _serialize_val(val) == _serialize_val_exec(val)

    d = date(2026, 1, 31)
    assert _serialize_val(d) == _serialize_val_exec(d)
