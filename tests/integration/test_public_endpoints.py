import pytest
from fastapi.testclient import TestClient

from presentation.main import app


@pytest.fixture(autouse=True)
def env_vars(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
    monkeypatch.setenv("CATALOG_SERVICE_URL", "http://catalog")


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_docs_accessible_without_auth(client):
    """FR-013: /docs must return 200 without Bearer token."""
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_redoc_accessible_without_auth(client):
    resp = client.get("/redoc")
    assert resp.status_code == 200


def test_health_accessible_without_auth(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
