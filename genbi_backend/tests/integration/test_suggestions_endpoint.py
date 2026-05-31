"""Tests d'intégration — GET /api/v1/suggestions (T046-T048)."""

SUGGESTIONS = "/api/v1/suggestions"


def test_suggestions_retourne_liste(client, auth_bourguiba):
    r = client.get(SUGGESTIONS, headers=auth_bourguiba)
    assert r.status_code == 200
    body = r.json()
    assert "suggestions" in body
    assert len(body["suggestions"]) >= 5


def test_suggestions_contient_questions_en_francais(client, auth_bourguiba):
    r = client.get(SUGGESTIONS, headers=auth_bourguiba)
    suggestions = r.json()["suggestions"]
    assert all(isinstance(s, str) and len(s) > 10 for s in suggestions)
    assert any("vente" in s.lower() or "produit" in s.lower() for s in suggestions)


def test_suggestions_sans_auth_retourne_401(client):
    r = client.get(SUGGESTIONS)
    assert r.status_code == 401
