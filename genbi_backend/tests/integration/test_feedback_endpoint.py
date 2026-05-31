"""Tests d'intégration — POST /api/v1/feedback (T049-T051)."""

FEEDBACK = "/api/v1/feedback"

_BODY_OK = {
    "question": "Quel est mon CA ce mois ?",
    "sql_generated": "SELECT SUM(total_amount_fcfa) FROM marts.fct_sales",
    "rating": "good",
    "comment": "Réponse correcte et rapide.",
}


def test_feedback_retourne_201(client, auth_bourguiba):
    r = client.post(FEEDBACK, json=_BODY_OK, headers=auth_bourguiba)
    assert r.status_code == 201
    body = r.json()
    assert "feedback_id" in body
    assert body["pharmacy_id"] == 1
    assert "created_at" in body


def test_feedback_sans_sql_ni_comment(client, auth_almadies):
    r = client.post(
        FEEDBACK,
        json={"question": "Top 5 produits ?", "rating": "bad"},
        headers=auth_almadies,
    )
    assert r.status_code == 201
    assert r.json()["pharmacy_id"] == 2


def test_feedback_rating_invalide_retourne_422(client, auth_bourguiba):
    r = client.post(
        FEEDBACK,
        json={**_BODY_OK, "rating": "excellent"},
        headers=auth_bourguiba,
    )
    assert r.status_code == 422


def test_feedback_sans_auth_retourne_401(client):
    r = client.post(FEEDBACK, json=_BODY_OK)
    assert r.status_code == 401


def test_feedback_stocke_bon_pharmacy_id(client, auth_nation):
    """La clé Nation → pharmacy_id=3 dans la ligne insérée."""
    r = client.post(
        FEEDBACK,
        json={"question": "Ruptures de stock ?", "rating": "good"},
        headers=auth_nation,
    )
    assert r.status_code == 201
    assert r.json()["pharmacy_id"] == 3
