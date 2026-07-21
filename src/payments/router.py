import stripe
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from src.auth.dependencies import require_role
from src.auth.models import Role, User
from src.db.config import settings
from src.db.database import get_db
from src.payments import service
from src.payments.models import PaymentStatus
from src.payments.schemas import (
    CheckoutRequest,
    CheckoutResponse,
    PaymentList,
    PaymentRead,
)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_checkout(
    data: CheckoutRequest,
    db: Session = Depends(get_db),
    manager: User = Depends(require_role(Role.MANAGER)),
):
    try:
        payment, checkout_url = service.create_checkout(
            db, manager, data.amount
        )
    except stripe.StripeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment provider is unavailable",
        )
    return CheckoutResponse(payment_id=payment.id, checkout_url=checkout_url)


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        event = stripe.Webhook.construct_event(
            payload=await request.body(),
            sig_header=request.headers.get("stripe-signature", ""),
            secret=settings.stripe_webhook_secret,
        )
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

    handlers = {
        "checkout.session.completed": service.complete_payment,
        "checkout.session.expired": service.expire_payment,
    }
    handler = handlers.get(event["type"])
    if handler is None:
        return {"status": "ignored"}
    session_obj = event["data"]["object"]
    metadata = session_obj["metadata"] if "metadata" in session_obj else None
    payment_id = (
        metadata["payment_id"]
        if metadata and "payment_id" in metadata
        else None
    )
    if payment_id is None or not payment_id.isdigit():
        return {"status": "ignored"}

    handler(db, int(payment_id))
    return {"status": "ok"}


@router.get("", response_model=PaymentList)
def list_payments(
    db: Session = Depends(get_db),
    manager: User = Depends(require_role(Role.MANAGER)),
    status_filter: PaymentStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items, total = service.list_payments(
        db,
        user_id=manager.id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return PaymentList(total=total, limit=limit, offset=offset, items=items)


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_role(Role.MANAGER)),
):
    payment = service.get_payment(db, payment_id)
    if payment is None or payment.user_id != manager.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    return payment
