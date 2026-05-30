import pytest
from pathlib import Path
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def manifest_path() -> Path:
    p = Path("dbt_project/target/manifest.json")
    if not p.exists():
        p = Path("../dbt_project/target/manifest.json")
    return p


@pytest.fixture
def auth_headers_bourguiba() -> dict:
    return {"X-API-Key": "pk_bourguiba_dev"}


@pytest.fixture
def auth_headers_almadies() -> dict:
    return {"X-API-Key": "pk_almadies_dev"}


@pytest.fixture
def client():
    from main import app
    return TestClient(app)
