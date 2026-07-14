"""Segment consumer + webhook fan-out."""

from __future__ import annotations

from sentiance.core.bus.memory import InMemoryEventBus
from sentiance.core.repositories.memory import InMemorySegmentRepository
from sentiance.core.schemas import TOPIC_SEGMENT, Activity, Segment
from sentiance.insights.service import SegmentConsumer, TimelineService


def _segment() -> Segment:
    return Segment(
        tenant_id="dev",
        user_id="u",
        device_id="d",
        activity=Activity.WALK,
        start=0.0,
        end=10.0,
        duration_s=10.0,
        distance_m=14.0,
        window_count=2,
    )


def test_consumer_persists_and_fans_out(
    bus: InMemoryEventBus, repo: InMemorySegmentRepository
) -> None:
    dispatched: list[Segment] = []
    SegmentConsumer(repo, sink=dispatched.append).register(bus)

    bus.publish(TOPIC_SEGMENT, key="u", value=_segment())
    bus.drain()

    assert len(dispatched) == 1
    assert TimelineService(repo).timeline("dev", "u")[0].distance_m == 14.0


def test_repository_is_idempotent(repo: InMemorySegmentRepository) -> None:
    seg = _segment()
    repo.add(seg)
    repo.add(seg)  # same event_id
    assert len(repo.list_for_user("dev", "u")) == 1
