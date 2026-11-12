"""Authentication routes: register and login."""

import asyncio

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from auth.jwt_handler import create_token
from auth.models import User
from auth.schemas import TokenResponse, UserCreate, UserLogin, UserOut
from database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


async def _hash_password(password: str) -> str:
    """Hash a password with bcrypt off the event loop."""
    hashed = await asyncio.to_thread(bcrypt.hashpw, password.encode(), bcrypt.gensalt())
    return hashed.decode()


async def _check_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash off the event loop."""
    return await asyncio.to_thread(bcrypt.checkpw, password.encode(), hashed.encode())


def _token_response(user: User) -> TokenResponse:
    """Build a TokenResponse for a user."""
    token = create_token(user.id, user.email, user.role)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Create a new user and return a JWT."""
    email = data.email.lower()
    try:
        existing = await db.scalar(select(User).where(User.email == email))
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
        user = User(email=email, name=data.name, hashed_password=await _hash_password(data.password))
        db.add(user)
        await db.commit()
        await db.refresh(user)
    except HTTPException:
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered") from None
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Database error") from None
    return _token_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Verify credentials and return a JWT."""
    try:
        user = await db.scalar(select(User).where(User.email == data.email.lower()))
    except SQLAlchemyError:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Database error") from None
    if user is None or not await _check_password(data.password, user.hashed_password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid email or password", headers={"WWW-Authenticate": "Bearer"}
        )
    return _token_response(user)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user."""
    return user
