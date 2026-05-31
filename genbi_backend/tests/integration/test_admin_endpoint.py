"""Tests d'intégration — POST /api/v1/admin/reload-manifest."""
import pytest


ADMIN_HEADERS = {"X-Admin-Secret": "test_admin_secret"}


@pytest.fixture(autouse=True)
def set_admin_secret(monkeypatch):
    """Injecte un secret admin pour la durée du test."""
    from config import settings
    monkeypatch.setattr(settings, "ADMIN_SECRET", "test_admin_secret")


def test_reload_sans_secret_retourne_403(client):
    res = client.post("/api/v1/admin/reload-manifest")
    assert res.status_code == 403


def test_reload_mauvais_secret_retourne_403(client):
    res = client.post("/api/v1/admin/reload-manifest", headers={"X-Admin-Secret": "mauvais"})
    assert res.status_code == 403


def test_reload_bon_secret_retourne_200(client):
    res = client.post("/api/v1/admin/reload-manifest", headers=ADMIN_HEADERS)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "reloaded"
    assert isinstance(body["manifest_models"], int)
    assert body["manifest_models"] > 0


def test_reload_desactive_si_secret_vide(client, monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "ADMIN_SECRET", "")
    res = client.post("/api/v1/admin/reload-manifest", headers=ADMIN_HEADERS)
    assert res.status_code == 403
