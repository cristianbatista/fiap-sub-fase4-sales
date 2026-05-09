from domain.entities.sale import Sale
from domain.repositories.sale_repository import SaleRepository

MAX_PAGE_SIZE = 100


class ListSoldVehicles:
    def __init__(self, repository: SaleRepository) -> None:
        self._repository = repository

    async def execute(self, page: int, page_size: int) -> tuple[list[Sale], int]:
        page_size = min(page_size, MAX_PAGE_SIZE)
        return await self._repository.list_completed(page=page, page_size=page_size)


__all__ = ["ListSoldVehicles"]
