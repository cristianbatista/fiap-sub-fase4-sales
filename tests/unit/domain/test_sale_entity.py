from datetime import UTC, date
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from domain.entities.sale import Sale, SaleStatus


def _make_sale(**kwargs) -> Sale:
    defaults = dict(
        vehicle_id="v1",
        vehicle_price_at_sale=Decimal("50000.00"),
        buyer_cpf="529.982.247-25",
        sale_date=date(2026, 5, 9),
    )
    defaults.update(kwargs)
    return Sale(**defaults)


def test_sale_status_is_str_enum():
    assert issubclass(SaleStatus, StrEnum)


def test_sale_status_string_values_match_data_model():
    assert SaleStatus.PENDING_PAYMENT == "pending_payment"
    assert SaleStatus.COMPLETED == "completed"
    assert SaleStatus.CANCELLED == "cancelled"


def test_default_status_is_pending_payment():
    sale = _make_sale()
    assert sale.status == SaleStatus.PENDING_PAYMENT


def test_payment_code_is_uuid():
    sale = _make_sale()
    assert isinstance(sale.payment_code, UUID)


def test_id_is_uuid():
    sale = _make_sale()
    assert isinstance(sale.id, UUID)


def test_two_sales_have_different_ids():
    s1 = _make_sale()
    s2 = _make_sale()
    assert s1.id != s2.id


def test_two_sales_have_different_payment_codes():
    s1 = _make_sale()
    s2 = _make_sale()
    assert s1.payment_code != s2.payment_code


def test_created_at_is_utc_aware():
    sale = _make_sale()
    assert sale.created_at.tzinfo is not None
    assert sale.created_at.tzinfo == UTC


def test_updated_at_is_utc_aware():
    sale = _make_sale()
    assert sale.updated_at.tzinfo is not None


def test_status_mutation_to_completed():
    sale = _make_sale()
    sale.status = SaleStatus.COMPLETED
    assert sale.status == SaleStatus.COMPLETED


def test_status_mutation_to_cancelled():
    sale = _make_sale()
    sale.status = SaleStatus.CANCELLED
    assert sale.status == SaleStatus.CANCELLED
