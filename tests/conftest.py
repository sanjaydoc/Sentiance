"""Shared fixtures."""

from __future__ import annotations

import pytest

from sentiance.core.bus.memory import InMemoryEventBus
from sentiance.core.repositories.memory import InMemorySegmentRepository
from sentiance.features import FeatureExtractor


@pytest.fixture
def bus() -> InMemoryEventBus:
    return InMemoryEventBus()


@pytest.fixture
def repo() -> InMemorySegmentRepository:
    return InMemorySegmentRepository()


@pytest.fixture
def extractor() -> FeatureExtractor:
    return FeatureExtractor(window_seconds=5.0, min_samples=16)
