from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from domain.entities.sale import Sale, SaleStatus
from presentation.main import app

SECRET = "test-secret"
ALGORITHM = "HS256"


def _token() -> str:
    return jwt.encode({"sub": "operator-1"}, SECRET, algorithm=ALGORITHM)


def _auth_header() -> dict:
    return {"Authorization": f"Bearer {_token()}"}


def _make_sale(price: str) -> Sale:
    sale = Sale(
        vehicle_id=str(uuid4()),
        vehicle_price_at_sale=Decimal(price),
        buyer_cpf="529.982.247-25",
        sale_date=date(2026, 5, 9),
    )
    sale.status = SaleStatus.COMPLETED
    return sale


@pytest.fixture(autouse=True)
def env_vars(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", ALGORITHM)
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
    monkeypatch.setenv("CATALOG_SERVICE_URL", "http://catalog")


@pytest.fixture()
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def _get(client, params: dict | None = None, headers: dict | None = None):
    return client.get(
        "/sales/sold", params=params or {}, headers=headers or _auth_header()
    )


# --- Happy path ---


def test_200_empty_list(client):
    mock_repo = AsyncMock()
    mock_repo.list_completed.return_value = ([], 0)

    with patch("presentation.routers.sales.SaleRepositoryImpl", return_value=mock_repo):
        resp = _get(client)

    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 20


def test_200_items_ordered_by_price_asc(client):
    cheap = _make_sale("20000.00")
    expensive = _make_sale("90000.00")
    mock_repo = AsyncMock()
    mock_repo.list_completed.return_value = ([cheap, expensive], 2)

    with patch("presentation.routers.sales.SaleRepositoryImpl", return_value=mock_repo):
        resp = _get(client)

    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 2
    assert float(items[0]["vehicle_price_at_sale"]) < float(
        items[1]["vehicle_price_at_sale"]
    )


def test_200_pagination_params_respected(client):
    mock_repo = AsyncMock()
    mock_repo.list_completed.return_value = ([], 0)

    with patch("presentation.routers.sales.SaleRepositoryImpl", return_value=mock_repo):
        resp = _get(client, params={"page": 2, "page_size": 5})

    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 2
    assert data["page_size"] == 5
    mock_repo.list_completed.assert_called_once_with(page=2, page_size=5)


# --- Auth errors ---


def test_401_without_token(client):
    resp = client.get("/sales/sold")
    assert resp.status_code == 401


# --- Validation errors ---


def test_422_when_page_size_exceeds_100(client):
    resp = _get(client, params={"page_size": 101})
    assert resp.status_code == 422
