"""Tests d'intégration — POST /api/v1/interpret (T038-T040)."""
from unittest.mock import patch, AsyncMock

INTERPRET = "/api/v1/interpret"
INSIGHT_MOCK = "Vous avez réalisé 1 617 ventes ce mois pour un CA de 15 M FCFA."

_RESULTS_OK = {
    "columns": ["total_ventes", "ca_fcfa"],
    "rows": [[1617, 15_000_000]],
}


def _mock_insight(text: str = INSIGHT_MOCK):
    return patch(
        "api.v1.interpret.service.generate_insight",
        new=AsyncMock(return_value=text),
    )


def test_interpret_retourne_insight(client, auth_bourguiba):
    with _mock_insight():
        r = client.post(
            INTERPRET,
            json={"question": "Quel est mon CA ?", "results": _RESULTS_OK},
            headers=auth_bourguiba,
        )
    assert r.status_code == 200
    assert r.json()["insight"] == INSIGHT_MOCK


def test_interpret_resultats_vides_retourne_400(client, auth_bourguiba):
    r = client.post(
        INTERPRET,
        json={"question": "Quel est mon CA ?", "results": {"columns": [], "rows": []}},
        headers=auth_bourguiba,
    )
    assert r.status_code == 400
    assert "error" in r.json()


def test_interpret_sans_auth_retourne_401(client):
    r = client.post(
        INTERPRET,
        json={"question": "Quel est mon CA ?", "results": _RESULTS_OK},
    )
    assert r.status_code == 401
