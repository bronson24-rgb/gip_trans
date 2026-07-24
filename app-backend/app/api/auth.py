import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import (
    InvalidGoogleTokenError,
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    verify_google_id_token,
)
from app.database import get_db
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    GoogleLoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenPairResponse,
)

logger = logging.getLogger("app.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _issue_token_pair(db: Session, user: User) -> tuple[str, str]:
    jti = uuid.uuid4()
    refresh_row = RefreshToken(
        id=jti,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expire_days),
    )
    db.add(refresh_row)
    db.commit()

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id, jti)
    return access_token, refresh_token


@router.post("/google", response_model=TokenPairResponse)
@limiter.limit(lambda: settings.rate_limit_auth)
def login_with_google(
    request: Request,
    payload: GoogleLoginRequest,
    db: Session = Depends(get_db),
) -> TokenPairResponse:
    try:
        email = verify_google_id_token(payload.id_token)
    except InvalidGoogleTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Не удалось проверить токен Google")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        logger.warning("Попытка входа с непригашённым email: %s", email)
        # Самостоятельная регистрация не предусмотрена — доступ даёт только
        # запись в allow-list, которую создаёт PO/бухгалтер через app-admin.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Этот email не приглашён в систему")
    if not user.is_allowed:
        logger.warning("Попытка входа заблокированного пользователя: %s", email)
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Доступ запрещён (нет в allow-list)")

    logger.info("Успешный вход: %s (роль %s)", user.email, user.role.value)
    access_token, refresh_token = _issue_token_pair(db, user)
    return TokenPairResponse(
        access_token=access_token, refresh_token=refresh_token, email=user.email, full_name=user.full_name
    )


@router.post("/refresh", response_model=AccessTokenResponse)
@limiter.limit(lambda: settings.rate_limit_auth)
def refresh_access_token(
    request: Request,
    payload: RefreshRequest,
    db: Session = Depends(get_db),
) -> AccessTokenResponse:
    try:
        user_id, jti = decode_refresh_token(payload.refresh_token)
    except InvalidTokenError:
        logger.warning("Refresh с недействительным токеном")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Недействительный refresh-токен")

    token_row = db.get(RefreshToken, jti)
    if token_row is None or token_row.user_id != user_id:
        logger.warning("Refresh с токеном без соответствующей записи в БД (user_id=%s)", user_id)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Недействительный refresh-токен")

    if token_row.revoked_at is not None:
        # Уже использованный (отозванный) refresh-токен предъявлен повторно —
        # похоже на кражу токена. Отзываем ВСЕ refresh-токены пользователя,
        # заставляя перелогиниться на всех устройствах.
        logger.warning(
            "Обнаружено повторное использование отозванного refresh-токена, user_id=%s — отзываю все токены",
            user_id,
        )
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
        ).update({"revoked_at": datetime.now(timezone.utc)})
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh-токен вже використаний, увійдіть повторно")

    if token_row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Термін дії refresh-токена сплив")

    user = db.get(User, user_id)
    if user is None or not user.is_allowed:
        logger.warning("Refresh для заблокированного/несуществующего пользователя user_id=%s", user_id)
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Доступ заборонено")

    # Ротация: старый refresh-токен помечаем использованным, выдаём новую пару.
    token_row.revoked_at = datetime.now(timezone.utc)
    db.commit()

    access_token, refresh_token = _issue_token_pair(db, user)
    return AccessTokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(lambda: settings.rate_limit_auth)
def logout(
    request: Request,
    payload: LogoutRequest,
    db: Session = Depends(get_db),
) -> None:
    try:
        _user_id, jti = decode_refresh_token(payload.refresh_token)
    except InvalidTokenError:
        # Токен уже мусорный/просроченный — с точки зрения клиента logout всё
        # равно успешен (сессии он лишится в любом случае).
        return

    token_row = db.get(RefreshToken, jti)
    if token_row is not None and token_row.revoked_at is None:
        token_row.revoked_at = datetime.now(timezone.utc)
        db.commit()
