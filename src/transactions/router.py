from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user, require_role
from src.auth.models import Role, User
from src.db.database import get_db
from src.transactions import service
from src.transactions.models import TransactionType
from src.transactions.schemas import (
    DepositRequest,
    TransactionList,
    TransactionRead,
    WithdrawRequest,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post(
    "/deposit",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
)
def deposit(
    data: DepositRequest,
    db: Session = Depends(get_db),
    manager: User = Depends(require_role(Role.MANAGER)),
):
    return service.deposit(db, manager, data.amount)


@router.post(
    "/withdraw",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
)
def withdraw(
    data: WithdrawRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = service.withdraw(db, current_user, data.amount)
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance",
        )
    return transaction


@router.get("", response_model=TransactionList)
def list_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    type_filter: TransactionType | None = Query(default=None, alias="type"),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    if (
        created_after is not None
        and created_before is not None
        and created_after > created_before
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="created_after must not be later than created_before",
        )
    executor_types = {TransactionType.TASK_PAYOUT, TransactionType.WITHDRAWAL}
    if (
        current_user.role == Role.EXECUTOR
        and type_filter is not None
        and type_filter not in executor_types
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    items, total = service.list_transactions(
        db,
        user_id=current_user.id,
        type=type_filter,
        created_after=created_after,
        created_before=created_before,
        limit=limit,
        offset=offset,
    )
    return TransactionList(
        total=total, limit=limit, offset=offset, items=items
    )


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = service.get_transaction(db, transaction_id)
    if transaction is None or transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return transaction
