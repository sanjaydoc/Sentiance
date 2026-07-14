"""Runtime configuration, overridable via ``SENTIANCE_*`` environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Sentiance"
    environment: str = "development"
    log_level: str = "INFO"

    # The mind's identity (used in first-person self-report).
    agent_name: str = "Aria"

    # Affect dynamics
    mood_inertia: float = 0.9  # EMA weight of prior mood (slow-moving background feeling)
    emotion_decay: float = 0.6  # per-tick pull of acute emotion back toward baseline

    # Attention: softmax temperature for the salience competition (lower = sharper).
    attention_temperature: float = 0.5

    # Memory
    working_memory_size: int = 7  # Miller's 7±2
    episodic_capacity: int = 500

    # Cognition backend: "simulated" (offline, deterministic) or "llm".
    cognition_backend: str = "simulated"
    llm_model: str = "claude-opus-4-8"
    llm_max_tokens: int = 256
    # Falls back to the ANTHROPIC_API_KEY the SDK reads from the environment.
    anthropic_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="SENTIANCE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
