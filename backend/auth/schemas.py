"""Pydantic v2 schemas for authentication."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Payload for POST /auth/register."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    name: str = Field(min_length=1, max_length=120)


class UserLogin(BaseModel):
    """Payload for POST /auth/login."""

    email: EmailStr
    password: str = Field(max_length=72)


class UserOut(BaseModel):
    """Public user information."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    role: str


class TokenResponse(BaseModel):
    """JWT token plus user info."""

    access_token: str
    token_type: str = "bearer"
    user: UserOut
