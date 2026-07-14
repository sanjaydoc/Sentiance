"""Repository ports and adapters for derived state."""

from sentiance.core.repositories.base import SegmentRepository
from sentiance.core.repositories.memory import InMemorySegmentRepository

__all__ = ["SegmentRepository", "InMemorySegmentRepository"]
