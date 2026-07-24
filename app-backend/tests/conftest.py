import os
import uuid
from datetime import date, time
from decimal import Decimal

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://gip:change-me@localhost:5432/gip_trans_test"
)
# Дефолтные лимиты (10/20 в минуту) рассчитаны на реальный трафик, а не на то, что
# тесты сами дергают эти эндпоинты десятки раз за один прогон. Здесь — заведомо
# большой потолок, чтобы rate limiting не влиял на остальные тесты; сам rate
# limiting отдельно и целенаправленно проверяется в test_rate_limiting.py
# (через monkeypatch конкретных, маленьких значений на время одного теста).
os.environ.setdefault("RATE_LIMIT_AUTH", "10000/minute")
os.environ.setdefault("RATE_LIMIT_UPLOADS", "10000/minute")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import create_access_token
from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle

engine = create_engine(settings.database_url)
TestSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session():
    """Каждый тест — в своей транзакции, откатывается после теста (изоляция без пересоздания схемы).

    Роуты сами вызывают db.commit() — чтобы это не фиксировало данные по-настоящему,
    сессия живёт внутри SAVEPOINT, который перезапускается после каждого commit
    (стандартный паттерн SQLAlchemy "join a session into an external transaction").
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db_session):
    # По умолчанию — admin, а не driver (как в реальной БД): большинство существующих
    # тестов проверяют саму бизнес-логику ресурса, а не RBAC, и не должны падать от
    # добавления ролей. Для тестов конкретно на RBAC роль передаётся явно.
    def _make_user(email: str = "driver@example.com", is_allowed: bool = True, role: UserRole = UserRole.admin) -> User:
        user = User(email=email, full_name="Тест Тестов", is_allowed=is_allowed, role=role)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make_user


@pytest.fixture
def make_vehicle(db_session):
    def _make_vehicle(plate_number: str = "A123BC77") -> Vehicle:
        vehicle = Vehicle(plate_number=plate_number, is_active=True)
        db_session.add(vehicle)
        db_session.commit()
        db_session.refresh(vehicle)
        return vehicle

    return _make_vehicle


@pytest.fixture
def auth_headers(make_user):
    user = make_user()
    token = create_access_token(user.id, user.email)
    return {"Authorization": f"Bearer {token}"}, user


@pytest.fixture
def headers_for(make_user):
    """Фабрика: headers_for(role=UserRole.driver, email="...") -> (headers, user) — для RBAC-тестов."""

    def _headers_for(role: UserRole, email: str = "user@example.com") -> tuple[dict, User]:
        user = make_user(email=email, role=role)
        token = create_access_token(user.id, user.email)
        return {"Authorization": f"Bearer {token}"}, user

    return _headers_for


@pytest.fixture
def valid_route_report_payload(make_vehicle):
    vehicle = make_vehicle()
    return {
        "vehicle_id": str(vehicle.id),
        "report_date": date(2026, 7, 24).isoformat(),
        "route_from": "Москва",
        "route_to": "Тверь",
        "odometer_start": 1000,
        "odometer_end": 1180,
        "fuel_end": "30.00",
        "departure_time": time(8, 0).isoformat(),
        "arrival_time": time(12, 0).isoformat(),
        "fuel_refills": [],
    }
