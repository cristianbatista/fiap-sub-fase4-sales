from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.sale import Sale


class SaleRepository(ABC):
    @abstractmethod
    async def save(self, sale: Sale) -> Sale: ...

    @abstractmethod
    async def find_by_id(self, sale_id: UUID) -> Sale | None: ...

    @abstractmethod
    async def find_by_payment_code(self, payment_code: UUID) -> Sale | None: ...

    @abstractmethod
    async def list_completed(
        self, page: int, page_size: int
    ) -> tuple[list[Sale], int]: ...
