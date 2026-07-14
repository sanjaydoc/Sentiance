"""Application configuration loaded from the environment."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings, overridable via ``SENTIANCE_*`` environment variables."""

    app_name: str = "Sentiance"
    environment: str = "development"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_prefix="SENTIANCE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()
