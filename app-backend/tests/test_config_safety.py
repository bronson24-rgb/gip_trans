import pytest

from app.core.config import DEFAULT_INSECURE_JWT_SECRET, Settings, assert_safe_for_production


def test_refuses_to_start_in_production_with_default_secret():
    unsafe = Settings(environment="production", jwt_secret=DEFAULT_INSECURE_JWT_SECRET)
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        assert_safe_for_production(unsafe)


def test_allows_production_with_custom_secret():
    safe = Settings(environment="production", jwt_secret="a-real-random-secret-not-the-default")
    assert_safe_for_production(safe)  # не должно кидать


def test_allows_development_with_default_secret():
    dev = Settings(environment="development", jwt_secret=DEFAULT_INSECURE_JWT_SECRET)
    assert_safe_for_production(dev)  # дев-режим — дефолтный секрет допустим
