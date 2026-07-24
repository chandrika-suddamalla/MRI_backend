from __future__ import annotations

import logging
from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services.user_store import UserStore

logger = logging.getLogger("market_research_api")

user_store = UserStore()


class AuthService:
    """Service containing authentication business logic."""

    def login(self, payload: LoginRequest) -> TokenResponse:
        """Validate credentials and issue a signed JWT access token."""
        logger.info("Login requested for %s", payload.email)

        stored_user = user_store.get_user(str(payload.email))
        if stored_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No account found for this email. Please register first.")

        if not verify_password(payload.password, stored_user["password"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        token = create_access_token(str(payload.email))
        user = UserOut(email=str(payload.email), role="Analyst")
        return TokenResponse(access_token=token, user=user)

    def register(self, payload: RegisterRequest) -> TokenResponse:
        """Create a new user account and return a signed JWT access token."""
        logger.info("Registration requested for %s", payload.email)

        try:
            user_store.create_user(str(payload.email), hash_password(payload.password))
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists") from exc

        token = create_access_token(str(payload.email))
        user = UserOut(email=str(payload.email), role="Analyst")
        return TokenResponse(access_token=token, user=user)
