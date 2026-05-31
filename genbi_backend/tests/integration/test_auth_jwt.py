"""
T523 — Tests intégration api/v1/auth/
Écrits AVANT l'implémentation (TDD red → green).
"""
AUTH = "/api/v1/auth"


# ─── Login ────────────────────────────────────────────────────────────────────

def test_login_ok_retourne_token(client):
    r = client.post(f"{AUTH}/login", json={"email": "bourguiba@pharma.sn", "password": "test123"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


def test_login_mauvais_password_retourne_401(client):
    r = client.post(f"{AUTH}/login", json={"email": "bourguiba@pharma.sn", "password": "mauvais"})
    assert r.status_code == 401


def test_login_email_inconnu_retourne_401(client):
    r = client.post(f"{AUTH}/login", json={"email": "inconnu@pharma.sn", "password": "test123"})
    assert r.status_code == 401


def test_login_admin_retourne_token(client):
    r = client.post(f"{AUTH}/login", json={"email": "admin@genbi.sn", "password": "admin123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


# ─── /me ──────────────────────────────────────────────────────────────────────

def test_me_avec_token_valide_retourne_infos(client):
    token = client.post(f"{AUTH}/login", json={"email": "almadies@pharma.sn", "password": "test123"}).json()["access_token"]
    r = client.get(f"{AUTH}/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "almadies@pharma.sn"
    assert body["pharmacy_id"] == 2
    assert body["role"] == "pharmacist"


def test_me_sans_token_retourne_401(client):
    r = client.get(f"{AUTH}/me")
    assert r.status_code == 401


def test_me_token_invalide_retourne_401(client):
    r = client.get(f"{AUTH}/me", headers={"Authorization": "Bearer FAUX_TOKEN"})
    assert r.status_code == 401


# ─── /refresh ─────────────────────────────────────────────────────────────────

def test_refresh_retourne_nouveau_token(client):
    token = client.post(f"{AUTH}/login", json={"email": "nation@pharma.sn", "password": "test123"}).json()["access_token"]
    r = client.post(f"{AUTH}/refresh", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    new_token = r.json()["access_token"]
    assert len(new_token) > 20


def test_refresh_sans_token_retourne_401(client):
    r = client.post(f"{AUTH}/refresh")
    assert r.status_code == 401
