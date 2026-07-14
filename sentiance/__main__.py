"""``python -m sentiance`` — run the all-in-one dev server, or a demo.

- ``python -m sentiance``        → serve the platform on :8000 (docs at /docs)
- ``python -m sentiance demo``   → run a synthetic commute through the pipeline
                                    in-process and print the resulting timeline
"""

from __future__ import annotations

import sys

from sentiance.core.bus.memory import InMemoryEventBus
from sentiance.core.repositories.memory import InMemorySegmentRepository
from sentiance.insights.service import SegmentConsumer, TimelineService
from sentiance.processing.pipeline import ProcessingPipeline
from sentiance.simulation.generator import simulate_day


def run_demo() -> None:
    bus = InMemoryEventBus()
    repo = InMemorySegmentRepository()
    pipeline = ProcessingPipeline(bus)
    pipeline.register()
    SegmentConsumer(repo).register(bus)

    for batch in simulate_day():
        bus.publish("sensor.raw", key=batch.device_id, value=batch)
        bus.drain()
    pipeline.flush()
    bus.drain()

    timeline = TimelineService(repo)
    print("Detected timeline (u_demo):")
    for seg in timeline.timeline("dev", "u_demo"):
        mode = f" [{seg.transport_mode.value}]" if seg.transport_mode else ""
        print(
            f"  {seg.start:8.1f}s → {seg.end:8.1f}s  {seg.activity.value:<7}{mode}"
            f"  {seg.distance_m/1000:6.2f} km  ({seg.window_count} windows)"
        )
    print("\nSummary:", timeline.summary("dev", "u_demo"))


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo()
        return

    import uvicorn

    from sentiance.core.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "sentiance.app:app",
        host="0.0.0.0",  # noqa: S104 - bind all interfaces for container use
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
