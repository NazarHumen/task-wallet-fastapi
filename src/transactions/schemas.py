from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.transactions.models import TransactionType


class DepositRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class WithdrawRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    type: TransactionType
    amount: Decimal
    balance_after: Decimal
    task_id: int | None
    created_at: datetime


class TransactionList(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[TransactionRead]
