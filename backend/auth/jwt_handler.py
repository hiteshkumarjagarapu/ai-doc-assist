"""JWT creation and verification (HS256, 24h expiry by default)."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from config import settings


def create_token(user_id: int, email: str, role: str) -> str:
    """Create a signed JWT with payload {user_id, email, role, exp}."""
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    payload = {"user_id": user_id, "email": email, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises ValueError if invalid or expired."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
    if "user_id" not in payload:
        raise ValueError("Malformed token payload")
    return payload
