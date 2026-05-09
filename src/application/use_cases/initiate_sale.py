from datetime import date
from decimal import Decimal

from domain.entities.sale import Sale
from domain.repositories.sale_repository import SaleRepository
from infrastructure.http.catalog_client import (
    CatalogClient,
)


class InitiateSale:
    def __init__(self, repository: SaleRepository, catalog: CatalogClient) -> None:
        self._repository = repository
        self._catalog = catalog

    async def execute(self, vehicle_id: str, buyer_cpf: str, sale_date: date) -> Sale:
        vehicle = await self._catalog.get_vehicle(vehicle_id)

        price = Decimal(str(vehicle["price"]))

        sale = Sale(
            vehicle_id=vehicle_id,
            vehicle_price_at_sale=price,
            buyer_cpf=buyer_cpf,
            sale_date=sale_date,
        )

        # Notify catalog before persisting; if catalog fails, no record is created.
        await self._catalog.update_vehicle_status(vehicle_id, "sold")

        return await self._repository.save(sale)


__all__ = ["InitiateSale"]
