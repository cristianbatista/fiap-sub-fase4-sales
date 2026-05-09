from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from domain.entities.sale import Sale, SaleStatus
from presentation.main import app


def _make_sale(status: SaleStatus = SaleStatus.PENDING_PAYMENT) -> Sale:
    sale = Sale(
        vehicle_id="v1",
        vehicle_price_at_sale=Decimal("50000.00"),
        buyer_cpf="529.982.247-25",
        sale_date=date(2026, 5, 9),
    )
    sale.status = status
    return sale


@pytest.fixture(autouse=True)
def env_vars(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
    monkeypatch.setenv("CATALOG_SERVICE_URL", "http://catalog")


@pytest.fixture()
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def _post(client, body: dict):
    return client.post("/webhook/payment", json=body)


# --- Happy path ---


def test_200_on_paid(client):
    sale = _make_sale()
    mock_repo = AsyncMock()
    mock_repo.find_by_payment_code.return_value = sale
    mock_repo.save.side_effect = lambda s: s
    mock_catalog = AsyncMock()

    with (
        patch(
            "presentation.routers.webhook.SaleRepositoryImpl", return_value=mock_repo
        ),
        patch("presentation.routers.webhook.CatalogClient", return_value=mock_catalog),
    ):
        resp = _post(client, {"payment_code": str(sale.payment_code), "status": "paid"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["sale_id"] == str(sale.id)


def test_200_on_cancelled(client):
    sale = _make_sale()
    mock_repo = AsyncMock()
    mock_repo.find_by_payment_code.return_value = sale
    mock_repo.save.side_effect = lambda s: s
    mock_catalog = AsyncMock()

    with (
        patch(
            "presentation.routers.webhook.SaleRepositoryImpl", return_value=mock_repo
        ),
        patch("presentation.routers.webhook.CatalogClient", return_value=mock_catalog),
    ):
        resp = _post(
            client, {"payment_code": str(sale.payment_code), "status": "cancelled"}
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "cancelled"


# --- Validation errors ---


def test_400_invalid_status_value(client):
    resp = _post(client, {"payment_code": str(uuid4()), "status": "invalid"})
    assert resp.status_code == 422


# --- Not found ---


def test_404_unknown_payment_code(client):
    mock_repo = AsyncMock()
    mock_repo.find_by_payment_code.return_value = None
    mock_catalog = AsyncMock()

    with (
        patch(
            "presentation.routers.webhook.SaleRepositoryImpl", return_value=mock_repo
        ),
        patch("presentation.routers.webhook.CatalogClient", return_value=mock_catalog),
    ):
        resp = _post(client, {"payment_code": str(uuid4()), "status": "paid"})

    assert resp.status_code == 404
    assert "pagamento" in resp.json()["detail"].lower()


# --- Conflict (not modifiable) ---


def test_409_on_already_completed(client):
    sale = _make_sale(SaleStatus.COMPLETED)
    mock_repo = AsyncMock()
    mock_repo.find_by_payment_code.return_value = sale
    mock_catalog = AsyncMock()

    with (
        patch(
            "presentation.routers.webhook.SaleRepositoryImpl", return_value=mock_repo
        ),
        patch("presentation.routers.webhook.CatalogClient", return_value=mock_catalog),
    ):
        resp = _post(client, {"payment_code": str(sale.payment_code), "status": "paid"})

    assert resp.status_code == 409
    assert "pendente" in resp.json()["detail"].lower()


def test_409_on_already_cancelled(client):
    sale = _make_sale(SaleStatus.CANCELLED)
    mock_repo = AsyncMock()
    mock_repo.find_by_payment_code.return_value = sale
    mock_catalog = AsyncMock()

    with (
        patch(
            "presentation.routers.webhook.SaleRepositoryImpl", return_value=mock_repo
        ),
        patch("presentation.routers.webhook.CatalogClient", return_value=mock_catalog),
    ):
        resp = _post(
            client, {"payment_code": str(sale.payment_code), "status": "cancelled"}
        )

    assert resp.status_code == 409
