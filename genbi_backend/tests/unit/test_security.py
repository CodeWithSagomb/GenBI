"""
T521 — Tests unitaires core/security.py
Écrits AVANT l'implémentation (TDD red → green).
"""
import pytest

from core.security import hash_password, verify_password, create_access_token, decode_access_token
from core.exceptions import AuthError


# ─── Mots de passe ────────────────────────────────────────────────────────────

def test_hash_password_retourne_chaine_non_vide():
    h = hash_password("secret")
    assert isinstance(h, str) and len(h) > 0


def test_hash_password_commence_par_2b():
    """Vérifie le format bcrypt $2b$."""
    assert hash_password("motdepasse").startswith("$2b$")


def test_verify_password_correcte_retourne_true():
    h = hash_password("bonjour")
    assert verify_password("bonjour", h) is True


def test_verify_password_incorrecte_retourne_false():
    h = hash_password("bonjour")
    assert verify_password("mauvais", h) is False


def test_deux_hash_du_meme_mot_de_passe_sont_differents():
    """bcrypt génère un sel aléatoire — chaque hash est unique."""
    h1 = hash_password("abc")
    h2 = hash_password("abc")
    assert h1 != h2


# ─── JWT ──────────────────────────────────────────────────────────────────────

def test_create_et_decode_token_roundtrip():
    payload = {"sub": "bourguiba@pharma.sn", "pharmacy_id": 1, "role": "pharmacist"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "bourguiba@pharma.sn"
    assert decoded["pharmacy_id"] == 1
    assert decoded["role"] == "pharmacist"


def test_token_contient_exp():
    token = create_access_token({"sub": "test"})
    decoded = decode_access_token(token)
    assert "exp" in decoded


def test_token_expire_leve_auth_error():
    token = create_access_token({"sub": "test"}, expires_delta_minutes=-1)
    with pytest.raises(AuthError):
        decode_access_token(token)


def test_token_falsifie_leve_auth_error():
    token = create_access_token({"sub": "test"})
    falsifie = token[:-5] + "XXXXX"
    with pytest.raises(AuthError):
        decode_access_token(falsifie)


def test_token_vide_leve_auth_error():
    with pytest.raises(AuthError):
        decode_access_token("")
