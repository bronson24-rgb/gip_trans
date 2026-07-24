"""
ВРЕМЕННАЯ заглушка авторизации.

Архитектура (п.7 gip-architecture.md) определяет: Google OAuth + allow-list
разрешённых email в БД приложения. Проверка id_token от Google — отдельная
задача, не входящая в объём формы отчёта водителя.

Пока что личность водителя передаётся заголовком X-User-Email. Годится только
для дев-окружения. TODO(auth): заменить тело функции на верификацию Google
id_token, оставив ту же сигнатуру (возврат User) — вызывающий код (роуты)
менять не придётся.
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User


def get_current_driver(
    x_user_email: str | None = Header(default=None, alias="X-User-Email"),
    db: Session = Depends(get_db),
) -> User:
    if not x_user_email:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Не передан X-User-Email (временная заглушка авторизации)")

    user = db.query(User).filter(User.email == x_user_email).first()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Пользователь не найден")
    if not user.is_allowed:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Доступ запрещён (нет в allow-list)")
    return user
