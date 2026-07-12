from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.auth.models import User
from src.transactions.models import Transaction, TransactionType


def record_transaction(
    db: Session,
    *,
    user: User,
    type: TransactionType,
    amount: Decimal,
    balance_after: Decimal,
    task_id: int | None = None,
) -> Transaction:
    # Only stages the row; the caller commits so the ledger entry is atomic
    # with the balance change it describes.
    transaction = Transaction(
        user_id=user.id,
        type=type,
        amount=amount,
        balance_after=balance_after,
        task_id=task_id,
    )
    db.add(transaction)
    return transaction


def get_transaction(db: Session, transaction_id: int) -> Transaction | None:
    return db.get(Transaction, transaction_id)


def deposit(db: Session, user: User, amount: Decimal) -> Transaction:
    user = db.get(User, user.id, with_for_update=True)
    user.balance += amount
    transaction = record_transaction(
        db,
        user=user,
        type=TransactionType.DEPOSIT,
        amount=amount,
        balance_after=user.balance,
    )
    db.commit()
    db.refresh(transaction)
    return transaction


def withdraw(db: Session, user: User, amount: Decimal) -> Transaction | None:
    user = db.get(User, user.id, with_for_update=True)
    if user.balance < amount:
        return None
    user.balance -= amount
    transaction = record_transaction(
        db,
        user=user,
        type=TransactionType.WITHDRAWAL,
        amount=-amount,
        balance_after=user.balance,
    )
    db.commit()
    db.refresh(transaction)
    return transaction


def list_transactions(
    db: Session,
    *,
    user_id: int | None = None,
    type: TransactionType | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Transaction], int]:
    conditions = []
    if user_id is not None:
        conditions.append(Transaction.user_id == user_id)
    if type is not None:
        conditions.append(Transaction.type == type)
    if created_after is not None:
        conditions.append(Transaction.created_at >= created_after)
    if created_before is not None:
        conditions.append(Transaction.created_at <= created_before)

    total = db.scalar(
        select(func.count()).select_from(Transaction).where(*conditions)
    )
    items = db.scalars(
        select(Transaction)
        .where(*conditions)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return list(items), total or 0
