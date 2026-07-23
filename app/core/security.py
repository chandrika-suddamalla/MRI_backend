from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt

from app.core.settings import settings

try:
    import bcrypt
except ImportError:  # pragma: no cover - optional dependency in some environments
    bcrypt = None

PBKDF2_ITERATIONS = 290_000
PBKDF2_SALT_BYTES = 16


def create_access_token(subject: str) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.secrets.get_jwt_secret(), algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    return jwt.decode(token, settings.secrets.get_jwt_secret(), algorithms=[settings.jwt_algorithm])


def hash_password(password: str) -> str:
    """Hash a plaintext password using PBKDF2-HMAC-SHA256."""
    salt = os.urandom(PBKDF2_SALT_BYTES)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    derived_key_b64 = base64.b64encode(derived_key).decode("ascii")
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_b64}${derived_key_b64}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 hash or legacy bcrypt hash."""
    if not hashed_password:
        return False

    if hashed_password.startswith("pbkdf2_sha256$"):
        parts = hashed_password.split("$")
        if len(parts) != 4:
            return False

        _, iterations_text, salt_b64, derived_key_b64 = parts
        try:
            iterations = int(iterations_text)
        except ValueError:
            return False

        try:
            salt = base64.b64decode(salt_b64.encode("ascii"))
            expected_key = base64.b64decode(derived_key_b64.encode("ascii"))
        except (ValueError, UnicodeError):
            return False

        computed_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(computed_key, expected_key)

    if bcrypt is not None and hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except ValueError:
            return False

    return False
