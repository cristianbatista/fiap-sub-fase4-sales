from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


@pytest.fixture(autouse=True)
def env_vars(monkeypatch):
    monkeypatch.setenv("CATALOG_SERVICE_URL", "http://catalog-test")


async def test_get_vehicle_returns_dict_on_200():
    from infrastructure.http.catalog_client import CatalogClient

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "v1",
        "price": "50000.00",
        "status": "available",
    }

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_response)):
        client = CatalogClient()
        result = await client.get_vehicle("v1")

    assert result["id"] == "v1"


async def test_get_vehicle_raises_not_found_on_404():
    from infrastructure.http.catalog_client import CatalogClient, VehicleNotFoundError

    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_response)):
        client = CatalogClient()
        with pytest.raises(VehicleNotFoundError):
            await client.get_vehicle("v99")


async def test_get_vehicle_raises_not_available_when_status_not_available():
    from infrastructure.http.catalog_client import (
        CatalogClient,
        VehicleNotAvailableError,
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "v1",
        "price": "50000.00",
        "status": "reserved",
    }

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_response)):
        client = CatalogClient()
        with pytest.raises(VehicleNotAvailableError):
            await client.get_vehicle("v1")


async def test_get_vehicle_raises_unavailable_on_request_error():
    from infrastructure.http.catalog_client import (
        CatalogClient,
        CatalogUnavailableError,
    )

    with patch(
        "httpx.AsyncClient.get",
        new=AsyncMock(side_effect=httpx.RequestError("timeout")),
    ):
        client = CatalogClient()
        with pytest.raises(CatalogUnavailableError):
            await client.get_vehicle("v1")


async def test_update_vehicle_status_retries_once_on_500():
    from infrastructure.http.catalog_client import CatalogClient

    error_response = MagicMock()
    error_response.status_code = 500
    ok_response = MagicMock()
    ok_response.status_code = 200

    call_count = 0

    async def fake_patch(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return error_response if call_count == 1 else ok_response

    with patch("httpx.AsyncClient.patch", new=fake_patch):
        client = CatalogClient()
        await client.update_vehicle_status("v1", "available")

    assert call_count == 2


async def test_update_vehicle_status_timeout_is_5_seconds():
    from infrastructure.http.catalog_client import CatalogClient

    client = CatalogClient()
    assert client._client.timeout.read == 5.0
