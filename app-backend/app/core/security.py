import uuid
from datetime import datetime, timedelta, timezone

import jwt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import settings

JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


class InvalidGoogleTokenError(Exception):
    pass


def verify_google_id_token(token: str) -> str:
    """Проверяет подпись и audience Google id_token, возвращает email.

    Кидает InvalidGoogleTokenError на любую проблему (просроченный токен,
    неверная подпись, чужой client_id) — детали причины наружу не отдаём.
    """
    try:
        payload = google_id_token.verify_oauth2_token(
            token, google_requests.Request(), settings.google_oauth_client_id
        )
    except Exception as exc:  # noqa: BLE001 — библиотека кидает разные типы на разные проблемы
        raise InvalidGoogleTokenError(str(exc)) from exc

    email = payload.get("email")
    if not email or not payload.get("email_verified"):
        raise InvalidGoogleTokenError("email отсутствует або не підтверджений Google")

    return email


class InvalidTokenError(Exception):
    pass


def create_access_token(user_id: uuid.UUID, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": ACCESS_TOKEN_TYPE,
        "jti": str(uuid.uuid4()),  # гарантирует уникальность токена даже при выпуске в ту же секунду
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: uuid.UUID, jti: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "jti": str(jti),
        "type": REFRESH_TOKEN_TYPE,
        "iat": now,
        "exp": now + timedelta(days=settings.jwt_refresh_expire_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID:
    """Возвращает user_id. Кидает InvalidTokenError на просрочку/подделку/чужой тип токена."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != ACCESS_TOKEN_TYPE:
            raise InvalidTokenError("очікувався access-токен")
        return uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise InvalidTokenError(str(exc)) from exc


def decode_refresh_token(token: str) -> tuple[uuid.UUID, uuid.UUID]:
    """Возвращает (user_id, jti). Не проверяет отзыв/использование — это на стороне БД (RefreshToken)."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != REFRESH_TOKEN_TYPE:
            raise InvalidTokenError("очікувався refresh-токен")
        return uuid.UUID(payload["sub"]), uuid.UUID(payload["jti"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise InvalidTokenError(str(exc)) from exc
