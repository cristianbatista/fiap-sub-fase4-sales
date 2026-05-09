from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

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


async def test_find_by_payment_code_returns_none_on_miss():
    from infrastructure.database.sale_repository_impl import SaleRepositoryImpl

    session = AsyncMock()
    session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=None)
    )

    repo = SaleRepositoryImpl(session)
    result = await repo.find_by_payment_code(uuid4())

    assert result is None


async def test_list_completed_orders_by_price_asc():
    from infrastructure.database.models import SaleModel, SaleStatusEnum
    from infrastructure.database.sale_repository_impl import SaleRepositoryImpl

    cheap = MagicMock(spec=SaleModel)
    cheap.id = uuid4()
    cheap.vehicle_id = "v1"
    cheap.vehicle_price_at_sale = Decimal("10000.00")
    cheap.buyer_cpf = "529.982.247-25"
    cheap.sale_date = date(2026, 5, 9)
    cheap.payment_code = uuid4()
    cheap.status = SaleStatusEnum.COMPLETED
    from datetime import UTC, datetime

    cheap.created_at = datetime.now(UTC)
    cheap.updated_at = datetime.now(UTC)

    expensive = MagicMock(spec=SaleModel)
    expensive.id = uuid4()
    expensive.vehicle_id = "v2"
    expensive.vehicle_price_at_sale = Decimal("90000.00")
    expensive.buyer_cpf = "529.982.247-25"
    expensive.sale_date = date(2026, 5, 9)
    expensive.payment_code = uuid4()
    expensive.status = SaleStatusEnum.COMPLETED
    expensive.created_at = datetime.now(UTC)
    expensive.updated_at = datetime.now(UTC)

    session = AsyncMock()
    count_result = MagicMock()
    count_result.scalar_one.return_value = 2
    list_result = MagicMock()
    list_result.scalars.return_value.all.return_value = [cheap, expensive]
    session.execute.side_effect = [count_result, list_result]

    repo = SaleRepositoryImpl(session)
    items, total = await repo.list_completed(page=1, page_size=20)

    assert total == 2
    assert items[0].vehicle_price_at_sale < items[1].vehicle_price_at_sale


async def test_save_persists_updated_status():
    from datetime import UTC, datetime

    from infrastructure.database.models import SaleModel, SaleStatusEnum
    from infrastructure.database.sale_repository_impl import SaleRepositoryImpl

    sale = _make_sale(SaleStatus.COMPLETED)

    existing_model = MagicMock(spec=SaleModel)
    existing_model.id = sale.id
    existing_model.vehicle_id = sale.vehicle_id
    existing_model.vehicle_price_at_sale = sale.vehicle_price_at_sale
    existing_model.buyer_cpf = sale.buyer_cpf
    existing_model.sale_date = sale.sale_date
    existing_model.payment_code = sale.payment_code
    existing_model.status = SaleStatusEnum.COMPLETED
    existing_model.created_at = datetime.now(UTC)
    existing_model.updated_at = datetime.now(UTC)

    session = AsyncMock()
    session.get.side_effect = [existing_model, existing_model]

    repo = SaleRepositoryImpl(session)
    await repo.save(sale)

    assert existing_model.status == SaleStatusEnum.COMPLETED
    session.commit.assert_called_once()
