from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from application.use_cases.process_payment_callback import (
    ProcessPaymentCallback,
    SaleNotFoundError,
    SaleNotModifiableError,
)
from domain.entities.sale import Sale, SaleStatus


def _make_sale(status: SaleStatus = SaleStatus.PENDING_PAYMENT) -> Sale:
    sale = Sale(
        vehicle_id="v1",
        vehicle_price_at_sale=Decimal("50000.00"),
        buyer_cpf="529.982.247-25",
        sale_date=date(2026, 5, 9),
    )
    sale.status = status
    return sale


def _make_use_case(repo=None, catalog=None):
    repo = repo or AsyncMock()
    catalog = catalog or AsyncMock()
    return ProcessPaymentCallback(repository=repo, catalog=catalog), repo, catalog


async def test_paid_transitions_sale_to_completed():
    sale = _make_sale()
    repo = AsyncMock()
    repo.find_by_payment_code.return_value = sale
    repo.save.side_effect = lambda s: s

    uc, _, catalog = _make_use_case(repo=repo)
    result = await uc.execute(sale.payment_code, "paid")

    assert result.status == SaleStatus.COMPLETED


async def test_paid_calls_catalog_with_sold():
    sale = _make_sale()
    repo = AsyncMock()
    repo.find_by_payment_code.return_value = sale
    repo.save.side_effect = lambda s: s
    catalog = AsyncMock()

    uc = ProcessPaymentCallback(repository=repo, catalog=catalog)
    await uc.execute(sale.payment_code, "paid")

    catalog.update_vehicle_status.assert_called_once_with(str(sale.vehicle_id), "sold")


async def test_paid_completes_even_if_catalog_fails():
    sale = _make_sale()
    repo = AsyncMock()
    repo.find_by_payment_code.return_value = sale
    repo.save.side_effect = lambda s: s
    catalog = AsyncMock()
    catalog.update_vehicle_status.side_effect = Exception("network failure")

    uc = ProcessPaymentCallback(repository=repo, catalog=catalog)

    with patch("application.use_cases.process_payment_callback.logger") as mock_logger:
        result = await uc.execute(sale.payment_code, "paid")

    assert result.status == SaleStatus.COMPLETED
    mock_logger.error.assert_called_once()


async def test_cancelled_transitions_sale_to_cancelled():
    sale = _make_sale()
    repo = AsyncMock()
    repo.find_by_payment_code.return_value = sale
    repo.save.side_effect = lambda s: s
    catalog = AsyncMock()

    uc = ProcessPaymentCallback(repository=repo, catalog=catalog)
    result = await uc.execute(sale.payment_code, "cancelled")

    assert result.status == SaleStatus.CANCELLED


async def test_cancelled_calls_catalog_restore_available():
    sale = _make_sale()
    repo = AsyncMock()
    repo.find_by_payment_code.return_value = sale
    repo.save.side_effect = lambda s: s
    catalog = AsyncMock()

    uc = ProcessPaymentCallback(repository=repo, catalog=catalog)
    await uc.execute(sale.payment_code, "cancelled")

    catalog.update_vehicle_status.assert_called_once_with(
        str(sale.vehicle_id), "available"
    )


async def test_sale_not_found_raises_error():
    repo = AsyncMock()
    repo.find_by_payment_code.return_value = None
    catalog = AsyncMock()

    uc = ProcessPaymentCallback(repository=repo, catalog=catalog)

    with pytest.raises(SaleNotFoundError):
        await uc.execute(uuid4(), "paid")


async def test_already_completed_raises_not_modifiable():
    sale = _make_sale(SaleStatus.COMPLETED)
    repo = AsyncMock()
    repo.find_by_payment_code.return_value = sale

    uc, _, _ = _make_use_case(repo=repo)

    with pytest.raises(SaleNotModifiableError) as exc_info:
        await uc.execute(sale.payment_code, "paid")

    assert exc_info.value.current_status == SaleStatus.COMPLETED


async def test_already_cancelled_raises_not_modifiable():
    sale = _make_sale(SaleStatus.CANCELLED)
    repo = AsyncMock()
    repo.find_by_payment_code.return_value = sale

    uc, _, _ = _make_use_case(repo=repo)

    with pytest.raises(SaleNotModifiableError):
        await uc.execute(sale.payment_code, "cancelled")


async def test_catalog_failure_on_cancelled_is_logged_but_does_not_raise():
    sale = _make_sale()
    repo = AsyncMock()
    repo.find_by_payment_code.return_value = sale
    repo.save.side_effect = lambda s: s
    catalog = AsyncMock()
    catalog.update_vehicle_status.side_effect = Exception("network failure")

    uc = ProcessPaymentCallback(repository=repo, catalog=catalog)

    with patch("application.use_cases.process_payment_callback.logger") as mock_logger:
        result = await uc.execute(sale.payment_code, "cancelled")

    assert result.status == SaleStatus.CANCELLED
    mock_logger.error.assert_called_once()
