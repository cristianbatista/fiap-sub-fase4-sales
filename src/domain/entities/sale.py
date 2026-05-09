from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4


class SaleStatus(StrEnum):
    PENDING_PAYMENT = "pending_payment"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Sale:
    vehicle_id: str
    vehicle_price_at_sale: Decimal
    buyer_cpf: str
    sale_date: date
    id: UUID = field(default_factory=uuid4)
    payment_code: UUID = field(default_factory=uuid4)
    status: SaleStatus = SaleStatus.PENDING_PAYMENT
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
