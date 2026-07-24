import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import InvalidTokenError, decode_access_token
from app.database import get_db
from app.models.user import User, UserRole

logger = logging.getLogger("app.auth")

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        logger.warning("Запрос без токена авторизации")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Отсутствует токен авторизации")

    try:
        user_id = decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        logger.warning("Недействительный access-токен: %s", exc)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Недействительный или просроченный токен")

    user = db.get(User, user_id)
    if user is None:
        logger.warning("Токен ссылается на несуществующего пользователя user_id=%s", user_id)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Пользователь не найден")
    if not user.is_allowed:
        logger.warning("Доступ запрещён (не в allow-list): %s", user.email)
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Доступ запрещён (нет в allow-list)")
    return user


def require_roles(*allowed_roles: UserRole):
    """Фабрика зависимостей: пускает только пользователей с одной из указанных ролей.

    Использование: Depends(require_roles(UserRole.accountant, UserRole.admin))
    — или, если ограничение действует на весь роутер целиком, в
    APIRouter(dependencies=[Depends(require_roles(...))]).
    """

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            logger.warning(
                "Недостаточно прав: %s (роль %s), требуется одна из %s",
                user.email,
                user.role.value,
                [r.value for r in allowed_roles],
            )
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Недостаточно прав для этого действия")
        return user

    return dependency
