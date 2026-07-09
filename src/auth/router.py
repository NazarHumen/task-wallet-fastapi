from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.auth import service
from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.auth.schemas import RefreshRequest, Token, UserCreate, UserRead
from src.auth.security import create_access_token
from src.db.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=Token, status_code=status.HTTP_201_CREATED
)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if service.get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )
    user = service.register_user(db, data)
    access_token = create_access_token(
        subject=user.email, role=user.role.value
    )
    refresh_token = service.create_refresh_token(db, user)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = service.authenticate_user(
        db, form_data.username, form_data.password
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        subject=user.email, role=user.role.value
    )
    refresh_token = service.create_refresh_token(db, user)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    token = service.get_active_refresh_token(db, data.refresh_token)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = service.get_user_by_id(db, token.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        subject=user.email, role=user.role.value
    )
    new_refresh_token = service.rotate_refresh_token(db, token, user)
    return Token(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: RefreshRequest, db: Session = Depends(get_db)):
    token = service.get_active_refresh_token(db, data.refresh_token)
    if token is not None:
        service.revoke_refresh_token(db, token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user
