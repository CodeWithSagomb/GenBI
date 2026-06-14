"""Tests d'intégration — GET /api/v1/alerts — Phase 2 alertes proactives."""
from unittest.mock import patch, AsyncMock

ALERTS = "/api/v1/alerts"
INSIGHT_MOCK = "Plusieurs produits sont sous le seuil de sécurité."


def test_alerts_retourne_200(client, auth_bourguiba):
    with patch("api.v1.alerts.service.generate_insight", new=AsyncMock(return_value=INSIGHT_MOCK)):
        r = client.get(ALERTS, headers=auth_bourguiba)
    assert r.status_code == 200


def test_alerts_structure_response(client, auth_bourguiba):
    with patch("api.v1.alerts.service.generate_insight", new=AsyncMock(return_value=INSIGHT_MOCK)):
        r = client.get(ALERTS, headers=auth_bourguiba)
    body = r.json()
    assert "alerts" in body
    assert isinstance(body["alerts"], list)
    assert len(body["alerts"]) == 3
    for alert in body["alerts"]:
        assert "id" in alert
        assert "severity" in alert
        assert "title" in alert
        assert "columns" in alert
        assert "rows" in alert
        assert "row_count" in alert
        assert "insight" in alert


def test_alerts_severity_valides(client, auth_bourguiba):
    with patch("api.v1.alerts.service.generate_insight", new=AsyncMock(return_value=INSIGHT_MOCK)):
        r = client.get(ALERTS, headers=auth_bourguiba)
    severities = {a["severity"] for a in r.json()["alerts"]}
    assert severities <= {"danger", "warning", "info"}


def test_alerts_insight_genere_si_rows(client, auth_bourguiba):
    """generate_insight ne doit être appelé que si row_count > 0."""
    call_count = {"n": 0}

    async def mock_insight(*args, **kwargs):
        call_count["n"] += 1
        return INSIGHT_MOCK

    with patch("api.v1.alerts.service.generate_insight", side_effect=mock_insight):
        r = client.get(ALERTS, headers=auth_bourguiba)

    alerts_with_rows = sum(1 for a in r.json()["alerts"] if a["row_count"] > 0)
    assert call_count["n"] == alerts_with_rows


def test_alerts_sans_auth_retourne_401(client):
    r = client.get(ALERTS)
    assert r.status_code == 401
