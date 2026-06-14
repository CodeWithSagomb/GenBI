"""Tests d'intégration — POST /api/v1/query — pipeline complet (T041-T045)."""
from unittest.mock import patch, AsyncMock

QUERY = "/api/v1/query"
SQL_MOCK = "SELECT COUNT(*) AS total FROM marts.fct_sales"
INSIGHT_MOCK = "Votre pharmacie a enregistré 1 617 ventes ce mois."


def _mock_llm(sql: str = SQL_MOCK, insight: str = INSIGHT_MOCK):
    """Double mock : génération SQL + insight."""
    return (
        patch("api.v1.query.service.generate_sql", new=AsyncMock(return_value=sql)),
        patch("api.v1.query.service.generate_insight", new=AsyncMock(return_value=insight)),
    )


def test_query_retourne_pipeline_complet(client, auth_bourguiba):
    sql_mock, ins_mock = _mock_llm()
    with sql_mock, ins_mock:
        r = client.post(
            QUERY,
            json={"question": "Combien de ventes ce mois ?"},
            headers=auth_bourguiba,
        )
    assert r.status_code == 200
    body = r.json()
    assert body["sql"] == SQL_MOCK
    assert body["insight"] == INSIGHT_MOCK
    assert body["row_count"] >= 1
    assert isinstance(body["columns"], list)
    assert isinstance(body["rows"], list)


def test_query_rls_isole_par_pharmacie(client, auth_bourguiba, auth_almadies):
    """Deux pharmacies → SQL identique → résultats différents (RLS actif)."""
    sql_mock_b, ins_mock_b = _mock_llm()
    with sql_mock_b, ins_mock_b:
        r1 = client.post(QUERY, json={"question": "Combien de ventes ?"}, headers=auth_bourguiba)

    sql_mock_a, ins_mock_a = _mock_llm()
    with sql_mock_a, ins_mock_a:
        r2 = client.post(QUERY, json={"question": "Combien de ventes ?"}, headers=auth_almadies)

    assert r1.status_code == 200
    assert r2.status_code == 200
    count_b = r1.json()["rows"][0][0]
    count_a = r2.json()["rows"][0][0]
    assert count_b > 0
    assert count_a > 0
    assert count_b != count_a or count_b + count_a <= 4716


def test_query_question_vide_retourne_422(client, auth_bourguiba):
    r = client.post(QUERY, json={"question": "  "}, headers=auth_bourguiba)
    assert r.status_code == 422


def test_query_sans_auth_retourne_401(client):
    r = client.post(QUERY, json={"question": "Quel est mon CA ?"})
    assert r.status_code == 401


def test_query_repare_sql_invalide(client, auth_bourguiba):
    """Phase 1 — Auto-repair : generate_sql retourne SQL cassé au 1er appel,
    repair_sql retourne SQL valide → la requête aboutit sans erreur 500."""
    SQL_CASSE = "SELECT * FROM fct_sales"  # schema manquant → psycopg2.Error réel
    call_count = {"n": 0}

    async def generate_sql_mock(*args, **kwargs):
        return SQL_CASSE

    async def repair_sql_mock(*args, **kwargs):
        call_count["n"] += 1
        return SQL_MOCK  # SQL valide renvoyé par le LLM après repair

    with (
        patch("api.v1.query.service.generate_sql", new=AsyncMock(side_effect=generate_sql_mock)),
        patch("api.v1.query.service.repair_sql", new=AsyncMock(side_effect=repair_sql_mock)),
        patch("api.v1.query.service.generate_insight", new=AsyncMock(return_value=INSIGHT_MOCK)),
    ):
        r = client.post(
            QUERY,
            json={"question": "Combien de ventes ?"},
            headers=auth_bourguiba,
        )

    assert r.status_code == 200
    assert call_count["n"] == 1, "repair_sql doit être appelé exactement 1 fois"
    assert r.json()["sql"] == SQL_MOCK


def test_query_llm_timeout_retourne_504(client, auth_bourguiba):
    from core.exceptions import LLMTimeoutError

    async def raises_timeout(*args, **kwargs):
        raise LLMTimeoutError("Ollama timeout")

    with patch("api.v1.query.service.generate_sql", side_effect=raises_timeout):
        r = client.post(
            QUERY,
            json={"question": "Quel est mon CA ?"},
            headers=auth_bourguiba,
        )
    assert r.status_code == 504
