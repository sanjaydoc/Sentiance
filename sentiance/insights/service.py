"""Read models and webhook dispatch for derived segments.

``SegmentConsumer`` subscribes to ``segment.detected``, persists each segment
(idempotently), and fans it out to a webhook sink. ``TimelineService`` serves
per-user timeline and daily-summary reads from the repository.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from sentiance.core.bus.base import EventBus, Message
from sentiance.core.repositories.base import SegmentRepository
from sentiance.core.schemas import TOPIC_SEGMENT, Segment

WebhookSink = Callable[[Segment], None]


def null_sink(_segment: Segment) -> None:
    """Default webhook sink: does nothing."""


class SegmentConsumer:
    """Persists segments and dispatches them to a webhook sink."""

    def __init__(
        self,
        repository: SegmentRepository,
        sink: WebhookSink = null_sink,
    ) -> None:
        self.repository = repository
        self.sink = sink

    def register(self, bus: EventBus) -> None:
        bus.subscribe(TOPIC_SEGMENT, self._on_segment)

    def _on_segment(self, message: Message) -> None:
        segment = message.value
        assert isinstance(segment, Segment)
        self.repository.add(segment)
        self.sink(segment)


class TimelineService:
    """Query side over the segment store."""

    def __init__(self, repository: SegmentRepository) -> None:
        self.repository = repository

    def timeline(
        self,
        tenant_id: str,
        user_id: str,
        since: float | None = None,
        until: float | None = None,
    ) -> list[Segment]:
        return self.repository.list_for_user(tenant_id, user_id, since, until)

    def summary(
        self,
        tenant_id: str,
        user_id: str,
        since: float | None = None,
        until: float | None = None,
    ) -> dict:
        segments = self.timeline(tenant_id, user_id, since, until)
        by_activity: dict[str, dict[str, float]] = defaultdict(
            lambda: {"count": 0, "duration_s": 0.0, "distance_m": 0.0}
        )
        for seg in segments:
            bucket = by_activity[seg.activity.value]
            bucket["count"] += 1
            bucket["duration_s"] += seg.duration_s
            bucket["distance_m"] += seg.distance_m
        return {
            "user_id": user_id,
            "segment_count": len(segments),
            "total_distance_m": sum(s.distance_m for s in segments),
            "by_activity": dict(by_activity),
        }
