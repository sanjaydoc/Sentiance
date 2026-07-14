"""End-to-end processing pipeline over the in-memory bus."""

from __future__ import annotations

from sentiance.core.bus.memory import InMemoryEventBus
from sentiance.core.schemas import (
    TOPIC_ACTIVITY,
    TOPIC_FEATURES,
    TOPIC_SEGMENT,
    TOPIC_SENSOR_RAW,
    Activity,
    Segment,
)
from sentiance.processing.pipeline import ProcessingPipeline
from sentiance.simulation.generator import simulate_day


def test_pipeline_produces_expected_timeline(bus: InMemoryEventBus) -> None:
    pipeline = ProcessingPipeline(bus)
    pipeline.register()

    for batch in simulate_day():  # walk → drive → walk
        bus.publish(TOPIC_SENSOR_RAW, key=batch.device_id, value=batch)
        bus.drain()
    pipeline.flush()
    bus.drain()

    # Every stage emitted onto its topic.
    assert bus.messages_on(TOPIC_FEATURES)
    assert bus.messages_on(TOPIC_ACTIVITY)

    segments = [m for m in bus.messages_on(TOPIC_SEGMENT) if isinstance(m, Segment)]
    assert [s.activity for s in segments] == [
        Activity.WALK,
        Activity.VEHICLE,
        Activity.WALK,
    ]
    # The vehicle leg covers the most ground.
    vehicle = next(s for s in segments if s.activity is Activity.VEHICLE)
    assert vehicle.distance_m > 1000.0
    assert vehicle.transport_mode is not None


def test_multiple_devices_do_not_interleave(bus: InMemoryEventBus) -> None:
    pipeline = ProcessingPipeline(bus)
    pipeline.register()

    for device in ("d_a", "d_b"):
        for batch in simulate_day(device_id=device, user_id=f"u_{device}"):
            bus.publish(TOPIC_SENSOR_RAW, key=batch.device_id, value=batch)
            bus.drain()
    pipeline.flush()
    bus.drain()

    segments = [m for m in bus.messages_on(TOPIC_SEGMENT) if isinstance(m, Segment)]
    devices = {s.device_id for s in segments}
    assert devices == {"d_a", "d_b"}
    # Each device produced its own 3-segment day.
    assert sum(s.device_id == "d_a" for s in segments) == 3
    assert sum(s.device_id == "d_b" for s in segments) == 3
