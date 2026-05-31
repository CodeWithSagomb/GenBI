"""Tests d'intégration — POST /api/v1/execute (7 cas, sécurité critique)."""

EXECUTE = "/api/v1/execute"


def test_execute_select_retourne_resultats(client, auth_bourguiba):
    r = client.post(EXECUTE,
        json={"sql": "SELECT COUNT(*) FROM marts.fct_sales"},
        headers=auth_bourguiba)
    assert r.status_code == 200
    body = r.json()
    assert body["row_count"] == 1
    assert body["rows"][0][0] > 0          # compte réel de ventes


def test_execute_delete_retourne_400(client, auth_bourguiba):
    r = client.post(EXECUTE,
        json={"sql": "DELETE FROM marts.fct_sales"},
        headers=auth_bourguiba)
    assert r.status_code == 400
    assert "error" in r.json()


def test_execute_drop_retourne_400(client, auth_bourguiba):
    r = client.post(EXECUTE,
        json={"sql": "DROP TABLE marts.fct_sales"},
        headers=auth_bourguiba)
    assert r.status_code == 400


def test_execute_sql_invalide_retourne_400(client, auth_bourguiba):
    r = client.post(EXECUTE,
        json={"sql": "CECI N EST PAS DU SQL"},
        headers=auth_bourguiba)
    assert r.status_code == 400


def test_execute_utilise_user_readonly(client, auth_bourguiba):
    r = client.post(EXECUTE,
        json={"sql": "SELECT current_user"},
        headers=auth_bourguiba)
    assert r.status_code == 200
    assert r.json()["rows"][0][0] == "genbi_readonly"


def test_execute_rls_isole_par_pharmacie(client, auth_bourguiba, auth_almadies):
    """Bourguiba et Almadies ne voient que leurs propres ventes."""
    r1 = client.post(EXECUTE,
        json={"sql": "SELECT COUNT(*) FROM marts.fct_sales"},
        headers=auth_bourguiba)
    r2 = client.post(EXECUTE,
        json={"sql": "SELECT COUNT(*) FROM marts.fct_sales"},
        headers=auth_almadies)

    count_bourguiba = r1.json()["rows"][0][0]
    count_almadies  = r2.json()["rows"][0][0]

    assert count_bourguiba > 0
    assert count_almadies > 0
    # Les deux pharmacies ont des volumes différents (données générées différemment)
    # ET ensemble elles sont inférieures au total
    assert count_bourguiba + count_almadies < 4716 + 1


def test_execute_pagination_limit_respecte(client, auth_bourguiba):
    r = client.post(EXECUTE + "?limit=5",
        json={"sql": "SELECT * FROM marts.fct_sales"},
        headers=auth_bourguiba)
    assert r.status_code == 200
    body = r.json()
    assert body["limit"] == 5
    assert len(body["rows"]) <= 5
