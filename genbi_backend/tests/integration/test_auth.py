"""Tests d'intégration — authentification API Key + rate limiting."""
PING = "/api/v1/ping"


def test_requete_sans_api_key_retourne_401(client):
    r = client.get(PING)
    assert r.status_code == 401


def test_api_key_invalide_retourne_401(client):
    r = client.get(PING, headers={"X-API-Key": "cle_inventee"})
    assert r.status_code == 401
    assert "error" in r.json()


def test_api_key_valide_bourguiba_retourne_200(client, auth_bourguiba):
    r = client.get(PING, headers=auth_bourguiba)
    assert r.status_code == 200
    assert r.json()["pharmacy_id"] == 1


def test_api_key_valide_almadies_retourne_pharmacy_id_2(client, auth_almadies):
    r = client.get(PING, headers=auth_almadies)
    assert r.status_code == 200
    assert r.json()["pharmacy_id"] == 2


def test_rate_limit_depasse_retourne_429(client):
    from core.auth import reset_rate_limit
    test_key = "pk_nation_dev"
    reset_rate_limit(test_key)

    headers = {"X-API-Key": test_key}
    # 10 requêtes → toutes 200
    for _ in range(10):
        r = client.get(PING, headers=headers)
        assert r.status_code == 200

    # 11ème → 429
    r = client.get(PING, headers=headers)
    assert r.status_code == 429
    assert "error" in r.json()

    # Reset pour ne pas polluer les autres tests
    reset_rate_limit(test_key)


# ─── Admin JWT sur endpoints protégés ────────────────────────────────────────

def _admin_token() -> str:
    from core.security import create_access_token
    return create_access_token({
        "sub": "admin@genbi.sn",
        "user_id": 4,
        "pharmacy_id": None,
        "role": "admin",
    })


def test_admin_jwt_sur_ping_retourne_403(client):
    """Admin sans pharmacy_id → 403 Forbidden, pas 401 (ne pas déclencher logout)."""
    r = client.get(PING, headers={"Authorization": f"Bearer {_admin_token()}"})
    assert r.status_code == 403
    assert "error" in r.json()


def test_admin_jwt_sur_chat_retourne_403(client):
    r = client.post(
        "/api/v1/chat",
        json={"question": "test"},
        headers={"Authorization": f"Bearer {_admin_token()}"},
    )
    assert r.status_code == 403


def test_pharmacist_jwt_sur_ping_retourne_200(client):
    """JWT pharmacien valide → 200 (vérification que le chemin JWT normal marche)."""
    from core.security import create_access_token
    tok = create_access_token({
        "sub": "bourguiba@pharma.sn",
        "user_id": 1,
        "pharmacy_id": 1,
        "role": "pharmacist",
    })
    r = client.get(PING, headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    assert r.json()["pharmacy_id"] == 1
