import enum
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Role(str, enum.Enum):
    MANAGER = "manager"
    EXECUTOR = "executor"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.EXECUTOR)
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2),
                                             default=Decimal("0"))
    reserved_balance: Mapped[Decimal] = mapped_column(Numeric(10, 2),
                                              default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=lambda: datetime.now(
                                                     timezone.utc))
