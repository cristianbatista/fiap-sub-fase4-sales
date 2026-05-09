from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from application.use_cases.initiate_sale import InitiateSale
from domain.entities.sale import Sale, SaleStatus
from infrastructure.http.catalog_client import (
    CatalogUnavailableError,
    VehicleNotAvailableError,
    VehicleNotFoundError,
)


def _make_use_case(
    catalog_mock=None, repo_mock=None
) -> tuple[InitiateSale, MagicMock, MagicMock]:
    repo = repo_mock or AsyncMock()
    catalog = catalog_mock or AsyncMock()
    return InitiateSale(repository=repo, catalog=catalog), repo, catalog


def _vehicle_payload(price: str = "50000.00", status_val: str = "available") -> dict:
    return {"id": str(uuid4()), "price": price, "status": status_val}


async def test_creates_sale_with_pending_payment_status():
    catalog = AsyncMock()
    catalog.get_vehicle.return_value = _vehicle_payload()
    catalog.update_vehicle_status.return_value = None

    repo = AsyncMock()
    repo.save.side_effect = lambda sale: sale

    uc, _, _ = _make_use_case(catalog_mock=catalog, repo_mock=repo)
    sale = await uc.execute("v1", "529.982.247-25", date(2026, 5, 9))

    assert isinstance(sale, Sale)
    assert sale.status == SaleStatus.PENDING_PAYMENT
    assert sale.vehicle_id == "v1"
    assert sale.vehicle_price_at_sale == Decimal("50000.00")
    assert sale.buyer_cpf == "529.982.247-25"


async def test_payment_code_is_generated():
    catalog = AsyncMock()
    catalog.get_vehicle.return_value = _vehicle_payload()
    catalog.update_vehicle_status.return_value = None

    repo = AsyncMock()
    repo.save.side_effect = lambda sale: sale

    uc, _, _ = _make_use_case(catalog_mock=catalog, repo_mock=repo)
    sale = await uc.execute("v1", "529.982.247-25", date(2026, 5, 9))

    assert sale.payment_code is not None


async def test_raises_vehicle_not_found():
    catalog = AsyncMock()
    catalog.get_vehicle.side_effect = VehicleNotFoundError("v99")

    uc, _, _ = _make_use_case(catalog_mock=catalog)

    with pytest.raises(VehicleNotFoundError):
        await uc.execute("v99", "529.982.247-25", date(2026, 5, 9))


async def test_raises_vehicle_not_available():
    catalog = AsyncMock()
    catalog.get_vehicle.side_effect = VehicleNotAvailableError("v1")

    uc, _, _ = _make_use_case(catalog_mock=catalog)

    with pytest.raises(VehicleNotAvailableError):
        await uc.execute("v1", "529.982.247-25", date(2026, 5, 9))


async def test_raises_catalog_unavailable_on_network_error():
    catalog = AsyncMock()
    catalog.get_vehicle.side_effect = CatalogUnavailableError("unreachable")

    uc, _, _ = _make_use_case(catalog_mock=catalog)

    with pytest.raises(CatalogUnavailableError):
        await uc.execute("v1", "529.982.247-25", date(2026, 5, 9))


async def test_catalog_update_status_called_with_sold():
    catalog = AsyncMock()
    catalog.get_vehicle.return_value = _vehicle_payload()
    catalog.update_vehicle_status.return_value = None

    repo = AsyncMock()
    repo.save.side_effect = lambda sale: sale

    uc, _, _ = _make_use_case(catalog_mock=catalog, repo_mock=repo)
    await uc.execute("v1", "529.982.247-25", date(2026, 5, 9))

    catalog.update_vehicle_status.assert_called_once_with("v1", "reserved")


async def test_repo_not_called_when_catalog_update_fails():
    catalog = AsyncMock()
    catalog.get_vehicle.return_value = _vehicle_payload()
    catalog.update_vehicle_status.side_effect = CatalogUnavailableError("fail")

    repo = AsyncMock()

    uc, _, _ = _make_use_case(catalog_mock=catalog, repo_mock=repo)

    with pytest.raises(CatalogUnavailableError):
        await uc.execute("v1", "529.982.247-25", date(2026, 5, 9))

    repo.save.assert_not_called()
