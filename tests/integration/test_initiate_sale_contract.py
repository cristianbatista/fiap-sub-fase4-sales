from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from presentation.main import app

SECRET = "test-secret"
ALGORITHM = "HS256"

VALID_CPF = "529.982.247-25"
INVALID_CPF = "111.111.111-11"

VEHICLE_ID = str(uuid4())


def _token() -> str:
    return jwt.encode({"sub": "operator-1"}, SECRET, algorithm=ALGORITHM)


def _auth_header() -> dict:
    return {"Authorization": f"Bearer {_token()}"}


def _vehicle_ok() -> dict:
    return {"id": VEHICLE_ID, "price": "75000.00", "status": "available"}


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


def _post(client, body: dict, headers: dict | None = None):
    return client.post("/sales", json=body, headers=headers or _auth_header())


# --- Happy path ---


def test_201_valid_sale(client):
    mock_repo = AsyncMock()
    mock_catalog = AsyncMock()
    mock_catalog.get_vehicle.return_value = _vehicle_ok()
    mock_catalog.update_vehicle_status.return_value = None

    with (
        patch("presentation.routers.sales.SaleRepositoryImpl", return_value=mock_repo),
        patch("presentation.routers.sales.CatalogClient", return_value=mock_catalog),
    ):
        mock_repo.save.side_effect = lambda sale: sale
        resp = _post(
            client,
            {
                "vehicle_id": VEHICLE_ID,
                "buyer_cpf": VALID_CPF,
                "sale_date": "2026-05-09",
            },
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending_payment"
    assert data["vehicle_id"] == VEHICLE_ID
    assert data["vehicle_price_at_sale"] == "75000.00"
    assert "payment_code" in data


# --- Auth errors ---


def test_401_without_token(client):
    resp = client.post(
        "/sales",
        json={
            "vehicle_id": VEHICLE_ID,
            "buyer_cpf": VALID_CPF,
            "sale_date": "2026-05-09",
        },
    )
    assert resp.status_code == 401


# --- Validation errors ---


def test_400_invalid_cpf(client):
    mock_catalog = AsyncMock()
    mock_catalog.get_vehicle.return_value = _vehicle_ok()

    with patch("presentation.routers.sales.CatalogClient", return_value=mock_catalog):
        resp = _post(
            client,
            {
                "vehicle_id": VEHICLE_ID,
                "buyer_cpf": INVALID_CPF,
                "sale_date": "2026-05-09",
            },
        )

    assert resp.status_code == 422
    body_text = resp.text.lower()
    assert "cpf" in body_text or "inválido" in body_text


# --- Catalog errors ---


def test_404_vehicle_not_found(client):
    from infrastructure.http.catalog_client import VehicleNotFoundError

    mock_catalog = AsyncMock()
    mock_catalog.get_vehicle.side_effect = VehicleNotFoundError(VEHICLE_ID)

    with patch("presentation.routers.sales.CatalogClient", return_value=mock_catalog):
        resp = _post(
            client,
            {
                "vehicle_id": VEHICLE_ID,
                "buyer_cpf": VALID_CPF,
                "sale_date": "2026-05-09",
            },
        )

    assert resp.status_code == 404
    assert "catálogo" in resp.json()["detail"].lower()


def test_409_vehicle_already_sold(client):
    from infrastructure.http.catalog_client import VehicleNotAvailableError

    mock_catalog = AsyncMock()
    mock_catalog.get_vehicle.side_effect = VehicleNotAvailableError(VEHICLE_ID)

    with patch("presentation.routers.sales.CatalogClient", return_value=mock_catalog):
        resp = _post(
            client,
            {
                "vehicle_id": VEHICLE_ID,
                "buyer_cpf": VALID_CPF,
                "sale_date": "2026-05-09",
            },
        )

    assert resp.status_code == 409
    assert "vendido" in resp.json()["detail"].lower()


def test_503_catalog_unreachable(client):
    from infrastructure.http.catalog_client import CatalogUnavailableError

    mock_catalog = AsyncMock()
    mock_catalog.get_vehicle.side_effect = CatalogUnavailableError("down")

    with patch("presentation.routers.sales.CatalogClient", return_value=mock_catalog):
        resp = _post(
            client,
            {
                "vehicle_id": VEHICLE_ID,
                "buyer_cpf": VALID_CPF,
                "sale_date": "2026-05-09",
            },
        )

    assert resp.status_code == 503
    assert "catálogo" in resp.json()["detail"].lower()
