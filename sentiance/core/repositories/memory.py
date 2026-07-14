"""In-memory ``SegmentRepository`` adapter for tests and local runs.

A Postgres adapter implements the same port for production (row-level tenant
isolation, indexed on ``(tenant_id, user_id, start)``); it is intentionally not
required to run the reference pipeline.
"""

from __future__ import annotations

from sentiance.core.repositories.base import SegmentRepository
from sentiance.core.schemas import Segment


class InMemorySegmentRepository(SegmentRepository):
    def __init__(self) -> None:
        self._by_id: dict[str, Segment] = {}

    def add(self, segment: Segment) -> None:
        # Idempotent on event_id (ADR-0002).
        self._by_id.setdefault(segment.event_id, segment)

    def list_for_user(
        self,
        tenant_id: str,
        user_id: str,
        since: float | None = None,
        until: float | None = None,
    ) -> list[Segment]:
        results = [
            s
            for s in self._by_id.values()
            if s.tenant_id == tenant_id
            and s.user_id == user_id
            and (since is None or s.end >= since)
            and (until is None or s.start <= until)
        ]
        return sorted(results, key=lambda s: s.start)
