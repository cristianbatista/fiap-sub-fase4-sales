import logging
from uuid import UUID

from domain.entities.sale import Sale, SaleStatus
from domain.repositories.sale_repository import SaleRepository
from infrastructure.http.catalog_client import CatalogClient

logger = logging.getLogger(__name__)


class SaleNotFoundError(Exception):
    def __init__(self, payment_code: UUID) -> None:
        self.payment_code = payment_code
        super().__init__(f"Sale with payment code {payment_code} not found")


class SaleNotModifiableError(Exception):
    def __init__(self, current_status: SaleStatus) -> None:
        self.current_status = current_status
        super().__init__(
            f"Sale is not in pending_payment status (current: {current_status})"
        )


class ProcessPaymentCallback:
    def __init__(self, repository: SaleRepository, catalog: CatalogClient) -> None:
        self._repository = repository
        self._catalog = catalog

    async def execute(self, payment_code: UUID, payment_status: str) -> Sale:
        sale = await self._repository.find_by_payment_code(payment_code)
        if sale is None:
            raise SaleNotFoundError(payment_code)

        if sale.status != SaleStatus.PENDING_PAYMENT:
            raise SaleNotModifiableError(sale.status)

        if payment_status == "paid":
            sale.status = SaleStatus.COMPLETED
            try:
                await self._catalog.update_vehicle_status(str(sale.vehicle_id), "sold")
            except Exception:
                logger.error(
                    "Failed to mark vehicle as sold in Catalog after payment confirmation",
                    extra={"sale_id": str(sale.id), "vehicle_id": str(sale.vehicle_id)},
                )

        elif payment_status == "cancelled":
            sale.status = SaleStatus.CANCELLED
            try:
                await self._catalog.update_vehicle_status(
                    str(sale.vehicle_id), "available"
                )
            except Exception:
                logger.error(
                    "Failed to restore vehicle status in Catalog after cancellation",
                    extra={"sale_id": str(sale.id), "vehicle_id": str(sale.vehicle_id)},
                )

        return await self._repository.save(sale)


__all__ = ["ProcessPaymentCallback", "SaleNotFoundError", "SaleNotModifiableError"]
