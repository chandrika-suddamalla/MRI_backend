from __future__ import annotations

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Request payload for login."""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Request payload for registration."""

    email: EmailStr
    password: str


class UserOut(BaseModel):
    """Public user information returned by the auth endpoint."""

    email: str
    role: str


class TokenResponse(BaseModel):
    """Authentication response payload."""

    access_token: str
    token_type: str = "Bearer"
    user: UserOut
