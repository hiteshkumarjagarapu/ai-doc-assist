from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from auth.jwt_handler import create_token, verify_token
from config import settings


def test_roundtrip():
    payload = verify_token(create_token(5, "a@b.com", "user"))
    assert (payload["user_id"], payload["email"], payload["role"]) == (5, "a@b.com", "user")


def test_expiry_is_24_hours():
    payload = verify_token(create_token(1, "a@b.com", "user"))
    remaining = datetime.fromtimestamp(payload["exp"], timezone.utc) - datetime.now(timezone.utc)
    assert timedelta(hours=23, minutes=59) < remaining <= timedelta(hours=24)


def test_tampered_token_rejected():
    token = create_token(1, "a@b.com", "user")
    with pytest.raises(ValueError):
        verify_token(token[:-2] + ("aa" if not token.endswith("aa") else "bb"))


def test_expired_token_rejected():
    expired = jwt.encode(
        {"user_id": 1, "exp": datetime.now(timezone.utc) - timedelta(seconds=5)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(ValueError):
        verify_token(expired)
