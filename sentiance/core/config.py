"""Runtime configuration, overridable via ``SENTIANCE_*`` environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Sentiance"
    environment: str = "development"
    log_level: str = "INFO"

    # Event bus: "memory" (in-process) or "kafka" (see ADR-0001/0002).
    bus_backend: str = "memory"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_group_id: str = "sentiance"

    # Segment store: unset → in-memory adapter; set → Postgres adapter (prod).
    postgres_dsn: str | None = None

    # Feature extraction (ADR-0003).
    window_seconds: float = 5.0
    min_samples_per_window: int = 16

    # Segmentation hysteresis: windows of a new activity required to switch.
    segment_switch_windows: int = 2

    model_config = SettingsConfigDict(
        env_prefix="SENTIANCE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
