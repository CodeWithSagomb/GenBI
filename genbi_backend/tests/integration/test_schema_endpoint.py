"""Tests d'intégration — GET /api/v1/schema"""

SCHEMA = "/api/v1/schema"


def test_schema_retourne_200(client, auth_bourguiba):
    r = client.get(SCHEMA, headers=auth_bourguiba)
    assert r.status_code == 200


def test_schema_sans_auth_retourne_401(client):
    r = client.get(SCHEMA)
    assert r.status_code == 401


def test_schema_contient_marts(client, auth_bourguiba):
    r = client.get(SCHEMA, headers=auth_bourguiba)
    body = r.json()
    assert "schema" in body
    assert "marts.fct_sales" in body["schema"]


def test_schema_exclut_raw(client, auth_bourguiba):
    r = client.get(SCHEMA, headers=auth_bourguiba)
    assert "Table: raw." not in r.json()["schema"]
