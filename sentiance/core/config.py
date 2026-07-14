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

    # Temperament — stable disposition (0..1). Different values → a different individual.
    temperament_curiosity: float = 0.5
    temperament_anxiety: float = 0.5
    temperament_optimism: float = 0.5
    # How readily lived experience reshapes those traits (0 = fixed personality,
    # higher = more plastic). Small on purpose: character shifts slowly.
    temperament_plasticity: float = 0.01
    # Where chat persists the mind across runs (defaults to ~/.sentiance/<name>.json).
    persist_path: str | None = None
    # If set, every deliberation is logged as a (prompt, state) → thought JSONL row
    # to this path — a self-labeled dataset for training a small model (Path A/B).
    trace_path: str | None = None

    # Affect dynamics
    mood_inertia: float = 0.9  # EMA weight of prior mood (slow-moving background feeling)
    emotion_decay: float = 0.6  # per-tick pull of acute emotion back toward baseline

    # Attention: softmax temperature for the salience competition (lower = sharper).
    attention_temperature: float = 0.5

    # Memory
    working_memory_size: int = 7  # Miller's 7±2
    episodic_capacity: int = 500

    # Cognition backend: "simulated" (offline), "llm" (Anthropic), or "ollama" (local).
    cognition_backend: str = "simulated"
    llm_max_tokens: int = 256
    # "llm" backend (Anthropic).
    llm_model: str = "claude-opus-4-8"
    # Falls back to the ANTHROPIC_API_KEY the SDK reads from the environment.
    anthropic_api_key: str | None = None
    # "ollama" backend (local models — no key, nothing leaves the machine).
    ollama_model: str = "qwen2.5:7b"
    ollama_base_url: str = "http://localhost:11434"

    # Associative memory: "none" (lexical recall) or "ollama" (embedding recall).
    embedding_backend: str = "none"
    embedding_model: str = "nomic-embed-text"

    model_config = SettingsConfigDict(
        env_prefix="SENTIANCE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
