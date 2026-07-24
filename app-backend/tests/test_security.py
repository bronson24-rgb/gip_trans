import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    InvalidTokenError,
    JWT_ALGORITHM,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)


def test_access_token_roundtrip():
    user_id = uuid.uuid4()
    token = create_access_token(user_id, "driver@example.com")

    assert decode_access_token(token) == user_id


def test_refresh_token_roundtrip():
    user_id = uuid.uuid4()
    jti = uuid.uuid4()
    token = create_refresh_token(user_id, jti)

    decoded_user_id, decoded_jti = decode_refresh_token(token)

    assert decoded_user_id == user_id
    assert decoded_jti == jti


def test_decode_access_token_rejects_garbage():
    with pytest.raises(InvalidTokenError):
        decode_access_token("this-is-not-a-jwt")


def test_decode_access_token_rejects_tampered_signature():
    token = create_access_token(uuid.uuid4(), "driver@example.com")
    tampered = token[:-4] + "aaaa"

    with pytest.raises(InvalidTokenError):
        decode_access_token(tampered)


def test_refresh_token_cannot_be_used_as_access_token():
    """Иначе долгоживущий refresh давал бы полноценный доступ к API напрямую."""
    user_id = uuid.uuid4()
    refresh_token = create_refresh_token(user_id, uuid.uuid4())

    with pytest.raises(InvalidTokenError):
        decode_access_token(refresh_token)


def test_access_token_cannot_be_used_as_refresh_token():
    access_token = create_access_token(uuid.uuid4(), "driver@example.com")

    with pytest.raises(InvalidTokenError):
        decode_refresh_token(access_token)


def test_decode_access_token_rejects_expired_token():
    now = datetime.now(timezone.utc)
    expired_payload = {
        "sub": str(uuid.uuid4()),
        "email": "driver@example.com",
        "type": "access",
        "iat": now - timedelta(minutes=20),
        "exp": now - timedelta(minutes=5),
    }
    expired_token = jwt.encode(expired_payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)

    with pytest.raises(InvalidTokenError):
        decode_access_token(expired_token)
