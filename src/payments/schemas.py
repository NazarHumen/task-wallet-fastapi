from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.payments.models import PaymentStatus


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class CheckoutResponse(BaseModel):
    payment_id: int
    checkout_url: str


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    amount: Decimal
    status: PaymentStatus
    transaction_id: int | None
    created_at: datetime


class PaymentList(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[PaymentRead]
