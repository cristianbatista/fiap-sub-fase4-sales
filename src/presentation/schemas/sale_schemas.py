from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, field_validator

from domain.entities.sale import SaleStatus


def _cpf_digits(cpf: str) -> str:
    return "".join(c for c in cpf if c.isdigit())


def _cpf_check_digit(digits: str, length: int) -> int:
    weights = range(length + 1, 1, -1)
    total = sum(int(d) * w for d, w in zip(digits[:length], weights, strict=False))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder


def validate_cpf(value: str) -> str:
    digits = _cpf_digits(value)
    if len(digits) != 11 or len(set(digits)) == 1:
        raise ValueError("CPF inválido.")
    if _cpf_check_digit(digits, 9) != int(digits[9]):
        raise ValueError("CPF inválido.")
    if _cpf_check_digit(digits, 10) != int(digits[10]):
        raise ValueError("CPF inválido.")
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


class SaleCreateRequest(BaseModel):
    vehicle_id: str
    buyer_cpf: str
    sale_date: date

    @field_validator("buyer_cpf")
    @classmethod
    def validate_buyer_cpf(cls, v: str) -> str:
        return validate_cpf(v)


class SaleResponse(BaseModel):
    id: UUID
    vehicle_id: str
    vehicle_price_at_sale: Decimal
    buyer_cpf: str
    sale_date: date
    payment_code: UUID
    status: SaleStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SoldListingResponse(BaseModel):
    items: list[SaleResponse]
    total: int
    page: int
    page_size: int
