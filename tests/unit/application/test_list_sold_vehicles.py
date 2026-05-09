from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

from application.use_cases.list_sold_vehicles import ListSoldVehicles
from domain.entities.sale import Sale, SaleStatus


def _make_sale(price: str) -> Sale:
    sale = Sale(
        vehicle_id="v1",
        vehicle_price_at_sale=Decimal(price),
        buyer_cpf="529.982.247-25",
        sale_date=date(2026, 5, 9),
    )
    sale.status = SaleStatus.COMPLETED
    return sale


async def test_returns_empty_list_when_no_completed_sales():
    repo = AsyncMock()
    repo.list_completed.return_value = ([], 0)

    uc = ListSoldVehicles(repository=repo)
    items, total = await uc.execute(page=1, page_size=20)

    assert items == []
    assert total == 0


async def test_returns_only_completed_sales_ordered_by_price():
    cheap = _make_sale("30000.00")
    expensive = _make_sale("80000.00")
    repo = AsyncMock()
    repo.list_completed.return_value = ([cheap, expensive], 2)

    uc = ListSoldVehicles(repository=repo)
    items, total = await uc.execute(page=1, page_size=20)

    assert total == 2
    assert items[0].vehicle_price_at_sale < items[1].vehicle_price_at_sale


async def test_passes_pagination_params_to_repository():
    repo = AsyncMock()
    repo.list_completed.return_value = ([], 0)

    uc = ListSoldVehicles(repository=repo)
    await uc.execute(page=3, page_size=10)

    repo.list_completed.assert_called_once_with(page=3, page_size=10)


async def test_page_size_capped_at_100():
    repo = AsyncMock()
    repo.list_completed.return_value = ([], 0)

    uc = ListSoldVehicles(repository=repo)
    await uc.execute(page=1, page_size=999)

    repo.list_completed.assert_called_once_with(page=1, page_size=100)
