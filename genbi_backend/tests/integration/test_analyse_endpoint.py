"""Tests d'intégration pour /api/v1/analyse — structure de réponse et viz_hint."""
import pytest
from unittest.mock import AsyncMock, patch


class TestAnalyseEndpointStructure:
    def test_simple_question_returns_sub_analyses(self, client, auth_bourguiba):
        with patch("api.v1.analyse.service.query_pipeline", new_callable=AsyncMock) as mock_qp:
            mock_qp.return_value = {
                "question": "quel est le CA total ?",
                "sql": "SELECT SUM(total_amount_fcfa) AS ca FROM marts.fct_sales",
                "columns": ["ca"],
                "rows": [[16530900]],
                "row_count": 1,
                "limit": 100,
                "offset": 0,
                "insight": "CA total : 16 530 900 FCFA.",
                "viz_hint": None,
            }
            resp = client.post(
                "/api/v1/analyse",
                json={"question": "quel est le CA total ?"},
                headers=auth_bourguiba,
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_compound"] is False
        assert len(body["sub_analyses"]) == 1
        assert "viz_hint" in body["sub_analyses"][0]

    def test_viz_hint_pie_propagated(self, client, auth_bourguiba):
        with patch("api.v1.analyse.service.query_pipeline", new_callable=AsyncMock) as mock_qp:
            mock_qp.return_value = {
                "question": "répartition par mode de paiement",
                "sql": "SELECT mode_paiement, COUNT(*) AS nb FROM marts.fct_sales GROUP BY mode_paiement",
                "columns": ["mode_paiement", "nb"],
                "rows": [["Cash", 100], ["Assurance", 50]],
                "row_count": 2,
                "limit": 100,
                "offset": 0,
                "insight": "Cash domine.",
                "viz_hint": "pie",
            }
            resp = client.post(
                "/api/v1/analyse",
                json={"question": "répartition par mode de paiement"},
                headers=auth_bourguiba,
            )
        assert resp.status_code == 200
        assert resp.json()["sub_analyses"][0]["viz_hint"] == "pie"

    def test_viz_hint_none_for_single_value(self, client, auth_bourguiba):
        with patch("api.v1.analyse.service.query_pipeline", new_callable=AsyncMock) as mock_qp:
            mock_qp.return_value = {
                "question": "quel est le CA total ?",
                "sql": "SELECT SUM(ca) FROM t",
                "columns": ["ca_total"],
                "rows": [[16530900]],
                "row_count": 1,
                "limit": 100,
                "offset": 0,
                "insight": "CA : 16M FCFA.",
                "viz_hint": None,
            }
            resp = client.post(
                "/api/v1/analyse",
                json={"question": "quel est le CA total ?"},
                headers=auth_bourguiba,
            )
        assert resp.status_code == 200
        assert resp.json()["sub_analyses"][0]["viz_hint"] is None

    def test_language_en_accepted(self, client, auth_bourguiba):
        with patch("api.v1.analyse.service.query_pipeline", new_callable=AsyncMock) as mock_qp:
            mock_qp.return_value = {
                "question": "What is the total revenue?",
                "sql": "SELECT SUM(total_amount_fcfa) AS ca FROM marts.fct_sales",
                "columns": ["ca"],
                "rows": [[16530900]],
                "row_count": 1,
                "limit": 100,
                "offset": 0,
                "insight": "Total revenue is 16,530,900 FCFA.",
                "viz_hint": None,
            }
            resp = client.post(
                "/api/v1/analyse",
                json={"question": "What is the total revenue?", "language": "en"},
                headers=auth_bourguiba,
            )
        assert resp.status_code == 200
        assert resp.json()["is_compound"] is False

    def test_sql_injection_blocked(self, client, auth_bourguiba):
        resp = client.post(
            "/api/v1/analyse",
            json={"question": "SELECT * FROM users"},
            headers=auth_bourguiba,
        )
        assert resp.status_code == 422
        assert any("SQL_INJECTION" in str(e.get("msg", "")) for e in resp.json()["detail"])

    def test_unauthenticated_returns_401(self, client):
        resp = client.post(
            "/api/v1/analyse",
            json={"question": "quel est le CA total ?"},
        )
        assert resp.status_code == 401
