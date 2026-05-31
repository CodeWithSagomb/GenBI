import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

# Résolution du manifest : Docker (/app/...) ou local (../dbt_project/...)
_docker_manifest = Path("/app/dbt_project/target/manifest.json")
_local_manifest = Path(__file__).parent.parent.parent / "dbt_project" / "target" / "manifest.json"
if not _docker_manifest.exists() and _local_manifest.exists():
    os.environ.setdefault("DBT_MANIFEST_PATH", str(_local_manifest))


@pytest.fixture(scope="session")
def client():
    """Client de test avec lifespan complet (manifest + pool DB initialisés)."""
    from main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def manifest_path() -> Path:
    p = Path("dbt_project/target/manifest.json")
    if not p.exists():
        p = Path("../dbt_project/target/manifest.json")
    return p


@pytest.fixture
def auth_bourguiba() -> dict:
    return {"X-API-Key": "pk_bourguiba_dev"}


@pytest.fixture
def auth_almadies() -> dict:
    return {"X-API-Key": "pk_almadies_dev"}


@pytest.fixture
def auth_nation() -> dict:
    return {"X-API-Key": "pk_nation_dev"}


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Réinitialise le rate limiter avant chaque test — isolation garantie."""
    from core.auth import reset_rate_limit
    reset_rate_limit()
    yield
