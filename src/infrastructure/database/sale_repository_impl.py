from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.sale import Sale, SaleStatus
from domain.repositories.sale_repository import SaleRepository
from infrastructure.database.models import SaleModel, SaleStatusEnum


def _to_entity(model: SaleModel) -> Sale:
    return Sale(
        id=model.id,
        vehicle_id=model.vehicle_id,
        vehicle_price_at_sale=Decimal(str(model.vehicle_price_at_sale)),
        buyer_cpf=model.buyer_cpf,
        sale_date=model.sale_date,
        payment_code=model.payment_code,
        status=SaleStatus(model.status.value),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_model(sale: Sale) -> SaleModel:
    return SaleModel(
        id=sale.id,
        vehicle_id=sale.vehicle_id,
        vehicle_price_at_sale=sale.vehicle_price_at_sale,
        buyer_cpf=sale.buyer_cpf,
        sale_date=sale.sale_date,
        payment_code=sale.payment_code,
        status=SaleStatusEnum(sale.status.value),
        created_at=sale.created_at,
        updated_at=sale.updated_at,
    )


class SaleRepositoryImpl(SaleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, sale: Sale) -> Sale:
        result = await self._session.get(SaleModel, sale.id)
        if result is None:
            model = _to_model(sale)
            self._session.add(model)
        else:
            result.status = SaleStatusEnum(sale.status.value)
            result.updated_at = datetime.now(UTC)
        await self._session.commit()
        saved = await self._session.get(SaleModel, sale.id)
        return _to_entity(saved)  # type: ignore[arg-type]

    async def find_by_id(self, sale_id: UUID) -> Sale | None:
        model = await self._session.get(SaleModel, sale_id)
        return _to_entity(model) if model else None

    async def find_by_payment_code(self, payment_code: UUID) -> Sale | None:
        result = await self._session.execute(
            select(SaleModel).where(SaleModel.payment_code == payment_code)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list_completed(self, page: int, page_size: int) -> tuple[list[Sale], int]:
        skip = (page - 1) * page_size

        count_result = await self._session.execute(
            select(func.count()).where(SaleModel.status == SaleStatusEnum.COMPLETED)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(SaleModel)
            .where(SaleModel.status == SaleStatusEnum.COMPLETED)
            .order_by(SaleModel.vehicle_price_at_sale.asc())
            .offset(skip)
            .limit(page_size)
        )
        models = result.scalars().all()
        return [_to_entity(m) for m in models], total
