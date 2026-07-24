"""Отдельный файл: намеренно занижает лимиты на время теста через monkeypatch
(остальные тесты используют щедрый лимит из RATE_LIMIT_* в conftest.py, чтобы
сама rate-limiting логика им не мешала).

limiter.reset() до и после — иначе счётчик запросов, накопленный другими
тестами на тот же (client_ip, endpoint), потёк бы в этот тест и наоборот.
"""

import pytest

from app.core.config import settings
from app.core.limiter import limiter


@pytest.fixture(autouse=True)
def _reset_limiter():
    limiter.reset()
    yield
    limiter.reset()


def test_auth_endpoint_returns_429_after_exceeding_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_auth", "3/minute")

    responses = [client.post("/api/auth/google", json={"id_token": "garbage"}) for _ in range(4)]

    statuses = [r.status_code for r in responses]
    assert statuses[:3] == [401, 401, 401]  # первые 3 — обычная обработка (невалидный токен)
    assert statuses[3] == 429  # 4-й — уже упёрлись в лимит


def test_auth_rate_limit_is_scoped_per_endpoint(client, monkeypatch):
    """Лимит на /google не должен блокировать /refresh — это разные бакеты."""
    monkeypatch.setattr(settings, "rate_limit_auth", "1/minute")

    client.post("/api/auth/google", json={"id_token": "garbage"})
    blocked = client.post("/api/auth/google", json={"id_token": "garbage"})
    other_endpoint = client.post("/api/auth/refresh", json={"refresh_token": "garbage"})

    assert blocked.status_code == 429
    assert other_endpoint.status_code == 401  # не 429 — свой лимит, ещё не исчерпан


def test_uploads_endpoint_returns_429_after_exceeding_limit(client, auth_headers, monkeypatch):
    headers, _user = auth_headers
    monkeypatch.setattr(settings, "rate_limit_uploads", "2/minute")

    responses = [
        client.post(
            "/api/uploads/receipt",
            files={"file": ("f.txt", b"not an image", "text/plain")},
            headers=headers,
        )
        for _ in range(3)
    ]

    statuses = [r.status_code for r in responses]
    assert statuses[:2] == [415, 415]  # тип файла отклонён, но это ещё не rate limit
    assert statuses[2] == 429
