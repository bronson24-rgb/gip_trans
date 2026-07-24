import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt

from app.core.config import settings
from app.core.security import JWT_ALGORITHM, decode_access_token
from app.models.refresh_token import RefreshToken


def _google_login(client, email: str):
    with patch("app.api.auth.verify_google_id_token", return_value=email):
        return client.post("/api/auth/google", json={"id_token": "fake"})


# --- успешный вход ---------------------------------------------------------


def test_login_allowed_user_gets_valid_token_pair(client, make_user, db_session):
    user = make_user(email="allowed@example.com")

    response = _google_login(client, "allowed@example.com")

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "allowed@example.com"
    assert decode_access_token(body["access_token"]) == user.id

    # refresh-токену соответствует запись в БД
    payload = jwt.decode(body["refresh_token"], options={"verify_signature": False})
    assert db_session.get(RefreshToken, uuid.UUID(payload["jti"])) is not None


# --- отказ неавторизованному пользователю -----------------------------------


def test_login_unknown_email_is_rejected(client):
    response = _google_login(client, "stranger@example.com")
    assert response.status_code == 403


def test_login_not_allowed_user_is_rejected(client, make_user):
    make_user(email="blocked@example.com", is_allowed=False)
    response = _google_login(client, "blocked@example.com")
    assert response.status_code == 403


def test_login_invalid_google_token_returns_401(client):
    response = client.post("/api/auth/google", json={"id_token": "garbage"})
    assert response.status_code == 401


# --- истечение access-токена -------------------------------------------------


def test_expired_access_token_is_rejected_by_protected_endpoint(client, make_user):
    user = make_user()
    now = datetime.now(timezone.utc)
    expired_token = jwt.encode(
        {
            "sub": str(user.id),
            "email": user.email,
            "type": "access",
            "iat": now - timedelta(minutes=20),
            "exp": now - timedelta(minutes=1),
        },
        settings.jwt_secret,
        algorithm=JWT_ALGORITHM,
    )

    response = client.get("/api/route-reports", headers={"Authorization": f"Bearer {expired_token}"})

    assert response.status_code == 401


# --- обновление через refresh-токен -----------------------------------------


def test_refresh_issues_new_working_access_token(client, make_user):
    make_user(email="allowed@example.com")
    login = _google_login(client, "allowed@example.com").json()

    response = client.post("/api/auth/refresh", json={"refresh_token": login["refresh_token"]})

    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["access_token"] != login["access_token"]
    assert new_tokens["refresh_token"] != login["refresh_token"]

    # новым access-токеном реально можно ходить в защищённые эндпоинты
    check = client.get("/api/route-reports", headers={"Authorization": f"Bearer {new_tokens['access_token']}"})
    assert check.status_code == 200


def test_refresh_rotates_and_rejects_reused_token(client, make_user):
    """Ротация: старый refresh-токен одноразовый. Повторное предъявление — отказ."""
    make_user(email="allowed@example.com")
    login = _google_login(client, "allowed@example.com").json()

    first_refresh = client.post("/api/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert first_refresh.status_code == 200

    second_attempt = client.post("/api/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert second_attempt.status_code == 401


def test_refresh_reuse_revokes_all_user_tokens(client, make_user, db_session):
    """Повторное использование уже потраченного refresh — сигнал кражи: отзываем всё, что у юзера есть."""
    user = make_user(email="allowed@example.com")
    login = _google_login(client, "allowed@example.com").json()

    client.post("/api/auth/refresh", json={"refresh_token": login["refresh_token"]})
    # второй (валидный, свежевыданный) токен пользователя тоже должен быть отозван реакцией на кражу
    second_login = _google_login(client, "allowed@example.com").json()

    client.post("/api/auth/refresh", json={"refresh_token": login["refresh_token"]})  # повторное использование

    still_valid = client.post("/api/auth/refresh", json={"refresh_token": second_login["refresh_token"]})
    assert still_valid.status_code == 401


def test_refresh_with_garbage_token_returns_401(client):
    response = client.post("/api/auth/refresh", json={"refresh_token": "not-a-jwt"})
    assert response.status_code == 401


def test_access_token_cannot_be_used_to_refresh(client, make_user):
    """Access-токен не должен приниматься эндпоинтом refresh (защита от подмены типа токена)."""
    make_user(email="allowed@example.com")
    login = _google_login(client, "allowed@example.com").json()

    response = client.post("/api/auth/refresh", json={"refresh_token": login["access_token"]})

    assert response.status_code == 401


# --- logout -------------------------------------------------------------


def test_logout_revokes_refresh_token(client, make_user):
    make_user(email="allowed@example.com")
    login = _google_login(client, "allowed@example.com").json()

    logout_response = client.post("/api/auth/logout", json={"refresh_token": login["refresh_token"]})
    assert logout_response.status_code == 204

    refresh_after_logout = client.post("/api/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert refresh_after_logout.status_code == 401


def test_logout_is_idempotent_and_never_errors_on_garbage(client):
    response = client.post("/api/auth/logout", json={"refresh_token": "garbage"})
    assert response.status_code == 204
