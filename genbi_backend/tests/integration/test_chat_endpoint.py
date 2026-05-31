"""Tests d'intégration — POST /api/v1/chat"""
from unittest.mock import patch, AsyncMock

CHAT = "/api/v1/chat"
SQL_MOCK = "SELECT SUM(total_amount_fcfa) FROM marts.fct_sales"


def _mock_llm(sql: str = SQL_MOCK):
    """Patch generate_sql pour éviter d'appeler Ollama dans les tests."""
    return patch(
        "api.v1.chat.service.generate_sql",
        new=AsyncMock(return_value=sql),
    )


def test_chat_retourne_200_avec_sql(client, auth_bourguiba):
    with _mock_llm():
        r = client.post(CHAT, json={"question": "Quel est mon CA ?"}, headers=auth_bourguiba)
    assert r.status_code == 200
    assert r.json()["sql"] == SQL_MOCK


def test_chat_question_vide_retourne_422(client, auth_bourguiba):
    r = client.post(CHAT, json={"question": "  "}, headers=auth_bourguiba)
    assert r.status_code == 422


def test_chat_sans_auth_retourne_401(client):
    r = client.post(CHAT, json={"question": "Quel est mon CA ?"})
    assert r.status_code == 401


def test_chat_retourne_structure_complete(client, auth_bourguiba):
    with _mock_llm():
        r = client.post(CHAT, json={"question": "Top 5 produits ?"}, headers=auth_bourguiba)
    body = r.json()
    assert "question" in body
    assert "sql" in body
    assert body["question"] == "Top 5 produits ?"
