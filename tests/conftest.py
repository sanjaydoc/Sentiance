"""Shared fixtures for the mind tests."""

from __future__ import annotations

import pytest

from sentiance.core.config import Settings
from sentiance.mind import Mind


@pytest.fixture
def settings() -> Settings:
    # Explicit defaults, isolated from the process environment.
    return Settings()


@pytest.fixture
def mind(settings: Settings) -> Mind:
    return Mind(settings=settings)
