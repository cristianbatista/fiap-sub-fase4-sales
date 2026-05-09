import enum
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Enum, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SaleStatusEnum(str, enum.Enum):
    PENDING_PAYMENT = "pending_payment"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SaleModel(Base):
    __tablename__ = "sales"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    vehicle_id: Mapped[str] = mapped_column(String, nullable=False)
    vehicle_price_at_sale: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    buyer_cpf: Mapped[str] = mapped_column(String(14), nullable=False)
    sale_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_code: Mapped[UUID] = mapped_column(unique=True, default=uuid4)
    status: Mapped[SaleStatusEnum] = mapped_column(
        Enum(SaleStatusEnum, name="sale_status"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        UniqueConstraint("payment_code", name="uq_sales_payment_code"),
        Index("ix_sales_status", "status"),
        Index("ix_sales_vehicle_price_at_sale", "vehicle_price_at_sale"),
    )
