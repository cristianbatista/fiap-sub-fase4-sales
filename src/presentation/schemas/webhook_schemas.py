from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from domain.entities.sale import SaleStatus


class WebhookPaymentRequest(BaseModel):
    payment_code: UUID
    status: Literal["paid", "cancelled"]


class WebhookPaymentResponse(BaseModel):
    sale_id: UUID
    payment_code: UUID
    status: SaleStatus
    updated_at: datetime
