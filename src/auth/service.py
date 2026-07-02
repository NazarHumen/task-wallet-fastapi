from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.auth import security
from src.auth.models import RefreshToken, User
from src.auth.schemas import UserCreate
from src.config import settings


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def register_user(db: Session, data: UserCreate) -> User:
    user = User(
        email=data.email,
        hashed_password=security.hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user is None:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user


def create_refresh_token(db: Session, user: User) -> str:
    raw_token = security.generate_refresh_token()
    token = RefreshToken(
        user_id=user.id,
        token_hash=security.hash_refresh_token(raw_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(token)
    db.commit()
    return raw_token


def get_active_refresh_token(db: Session, raw_token: str) -> RefreshToken | None:
    token_hash = security.hash_refresh_token(raw_token)
    token = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    if token is None or token.revoked:
        return None
    if token.expires_at < datetime.now(timezone.utc):
        return None
    return token


def revoke_refresh_token(db: Session, token: RefreshToken) -> None:
    token.revoked = True
    db.commit()


def rotate_refresh_token(db: Session, token: RefreshToken, user: User) -> str:
    token.revoked = True
    raw_token = security.generate_refresh_token()
    new_token = RefreshToken(
        user_id=user.id,
        token_hash=security.hash_refresh_token(raw_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(new_token)
    db.commit()
    return raw_token
