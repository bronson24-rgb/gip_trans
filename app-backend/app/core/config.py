from pydantic_settings import BaseSettings, SettingsConfigDict

# Вынесено в константу: используется и как дефолт поля, и для проверки
# "секрет не сменили перед продом" в assert_safe_for_production().
DEFAULT_INSECURE_JWT_SECRET = "dev-insecure-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://gip:gip@localhost:5432/gip_trans"
    environment: str = "development"
    cors_allow_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8080",
        "http://localhost:8081",
    ]

    log_level: str = "INFO"

    # Google OAuth — см. docs/admin-guide.md за инструкцией по созданию Client ID.
    google_oauth_client_id: str = ""

    # JWT, которым backend подписывает собственную сессию после проверки Google id_token.
    # Access — короткоживущий, летит в каждом запросе к API. Refresh — долгоживущий,
    # используется только для получения нового access (и ротируется при каждом
    # использовании — см. app/api/auth.py и модель RefreshToken).
    jwt_secret: str = DEFAULT_INSECURE_JWT_SECRET
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 30

    # S3-совместимое хранилище (фото чеков). В деве — MinIO из infra/docker-compose.yml.
    # s3_endpoint_url — которым backend сам стучится в хранилище (внутри docker-сети
    # это "http://minio:9000"); s3_public_endpoint_url — хост, который должен быть
    # доступен из браузера пользователя, вшивается в presigned-ссылки (в деве —
    # "http://localhost:9000" — то же MinIO, но через порт, опубликованный на хост).
    s3_endpoint_url: str = "http://localhost:9000"
    s3_public_endpoint_url: str = "http://localhost:9000"
    s3_bucket: str = "gip-trans-receipts"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_region: str = "us-east-1"

    # Rate limiting (slowapi, формат строки — см. https://limits.readthedocs.io).
    # По IP клиента. In-memory хранилище — верно для одного инстанса backend
    # (текущая архитектура); при горизонтальном масштабировании потребует Redis.
    rate_limit_auth: str = "10/minute"
    rate_limit_uploads: str = "20/minute"


settings = Settings()


def assert_safe_for_production(settings: Settings) -> None:
    """Не даёт процессу стартовать в проде с секретом из репозитория."""
    if settings.environment == "production" and settings.jwt_secret == DEFAULT_INSECURE_JWT_SECRET:
        raise RuntimeError(
            "JWT_SECRET равен небезопасному значению по умолчанию, а ENVIRONMENT=production. "
            "Сгенерируйте случайный секрет (например: openssl rand -hex 32) и задайте его "
            "в JWT_SECRET в .env перед запуском в production."
        )
