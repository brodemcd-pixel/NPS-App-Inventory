"""Application settings (env-driven, see CONTRACT.md §11 / .env.example)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://players:players@localhost:5432/players"
    test_database_url: str = "postgresql+asyncpg://players:players@localhost:5432/players_test"
    secret_key: str = "change-me"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    players_encoder: str = "lite"
    web_base_url: str = "http://localhost:3000"
    backend_cors_origins: str = "http://localhost:3000"
    slack_bot_token: str = ""
    slack_signing_secret: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
