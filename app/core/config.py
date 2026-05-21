from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "poca-loop"
    environment: str = "local"
    secret_key: str = Field(min_length=16)
    access_token_expire_minutes: int = 60
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    seed_admin_email: str = "admin@example.com"
    seed_admin_username: str = "admin"
    seed_admin_password: str = Field(default="change-this-admin-password", min_length=8)
    backend_cors_origins: str = "http://localhost:3000,http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
