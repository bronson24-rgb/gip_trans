from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://gip:gip@localhost:5432/gip_trans"
    environment: str = "development"
    cors_allow_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
