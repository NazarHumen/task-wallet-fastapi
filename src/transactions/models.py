import enum
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TASK_RESERVE = "task_reserve"
    TASK_RESERVE_ADJUST = "task_reserve_adjust"
    TASK_PAYOUT = "task_payout"
    TASK_REFUND = "task_refund"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType), index=True
    )
    # Signed: negative for an outflow, positive for an inflow of available
    # balance.
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # Snapshot of the user's available balance right after this transaction.
    balance_after: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # Kept nullable with SET NULL so history survives a deleted task.
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"),
        index=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
