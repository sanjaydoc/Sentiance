"""The ``SegmentRepository`` port — persistence of derived segments."""

from __future__ import annotations

from abc import ABC, abstractmethod

from sentiance.core.schemas import Segment


class SegmentRepository(ABC):
    """Stores segments and serves per-user timeline reads.

    Writes are idempotent on ``event_id`` (ADR-0002): re-delivering the same
    segment must not create a duplicate.
    """

    @abstractmethod
    def add(self, segment: Segment) -> None:
        ...

    @abstractmethod
    def list_for_user(
        self,
        tenant_id: str,
        user_id: str,
        since: float | None = None,
        until: float | None = None,
    ) -> list[Segment]:
        ...
