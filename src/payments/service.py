from datetime import datetime, timedelta, timezone
from decimal import Decimal

import stripe
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.auth.models import User
from src.db.config import settings
from src.payments.models import Payment, PaymentStatus
from src.transactions.models import TransactionType
from src.transactions.service import record_transaction

stripe.api_key = settings.stripe_secret_key

CURRENCY = "usd"
CHECKOUT_TTL = timedelta(minutes=30)


def create_checkout(
    db: Session, user: User, amount: Decimal
) -> tuple[Payment, str]:
    payment = Payment(user_id=user.id, amount=amount)
    db.add(payment)
    db.commit()
    db.refresh(payment)

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": CURRENCY,
                        "product_data": {"name": "TaskWallet balance top-up"},
                        "unit_amount": int(amount * 100),
                    },
                    "quantity": 1,
                }
            ],
            metadata={"user_id": str(user.id), "payment_id": str(payment.id)},
            expires_at=int(
                (datetime.now(timezone.utc) + CHECKOUT_TTL).timestamp()
            ),
            adaptive_pricing={"enabled": False},
            success_url=settings.stripe_success_url,
            cancel_url=settings.stripe_cancel_url,
        )
    except stripe.StripeError:
        db.delete(payment)
        db.commit()
        raise

    payment.stripe_session_id = session.id
    db.commit()
    db.refresh(payment)
    return payment, session.url


def complete_payment(db: Session, payment_id: int) -> Payment | None:
    payment = db.get(Payment, payment_id, with_for_update=True)
    if payment is None or payment.status != PaymentStatus.PENDING:
        return None

    user = db.get(User, payment.user_id, with_for_update=True)
    if user is None:
        return None

    user.balance += payment.amount
    transaction = record_transaction(
        db,
        user=user,
        type=TransactionType.DEPOSIT,
        amount=payment.amount,
        balance_after=user.balance,
    )
    db.flush()

    payment.status = PaymentStatus.SUCCEEDED
    payment.transaction_id = transaction.id
    db.commit()
    db.refresh(payment)
    return payment


def expire_payment(db: Session, payment_id: int) -> Payment | None:
    payment = db.get(Payment, payment_id, with_for_update=True)
    if payment is None or payment.status != PaymentStatus.PENDING:
        return None
    payment.status = PaymentStatus.EXPIRED
    db.commit()
    db.refresh(payment)
    return payment


def get_payment(db: Session, payment_id: int) -> Payment | None:
    return db.get(Payment, payment_id)


def list_payments(
    db: Session,
    *,
    user_id: int,
    status: PaymentStatus | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Payment], int]:
    conditions = [Payment.user_id == user_id]
    if status is not None:
        conditions.append(Payment.status == status)

    total = db.scalar(
        select(func.count()).select_from(Payment).where(*conditions)
    )
    items = db.scalars(
        select(Payment)
        .where(*conditions)
        .order_by(Payment.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return list(items), total or 0
