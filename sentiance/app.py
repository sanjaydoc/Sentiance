"""All-in-one dev server: the full platform in a single process.

Wires ingestion → processing → insights onto one in-memory bus so the whole
pipeline is runnable and demonstrable without Kafka or Postgres (ADR-0001). Each
uploaded batch is treated as a session: after ingest we drain the bus and flush
open segments so the timeline is immediately queryable. The Kafka-backed
services (``ingestion.app`` / ``processing.worker`` / ``insights.app``) run the
same domain code without the per-batch flush.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from sentiance import __version__
from sentiance.core.bus.memory import InMemoryEventBus
from sentiance.core.repositories.memory import InMemorySegmentRepository
from sentiance.core.schemas import Segment, SensorBatch
from sentiance.ingestion.service import IngestionService
from sentiance.insights.service import SegmentConsumer, TimelineService
from sentiance.processing.pipeline import ProcessingPipeline
from sentiance.simulation.generator import simulate_day


def create_app() -> FastAPI:
    app = FastAPI(title="Sentiance Platform (all-in-one)", version=__version__)

    bus = InMemoryEventBus()
    repo = InMemorySegmentRepository()
    pipeline = ProcessingPipeline(bus)
    pipeline.register()
    SegmentConsumer(repo).register(bus)
    ingestion = IngestionService(bus)
    timeline = TimelineService(repo)

    # Exposed for tests / introspection.
    app.state.bus = bus
    app.state.repo = repo
    app.state.pipeline = pipeline

    def _process(batch: SensorBatch) -> None:
        ingestion.ingest(batch)
        bus.drain()
        pipeline.flush()
        bus.drain()

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__, "app": "sentiance"}

    @app.post("/v1/batches", tags=["ingestion"])
    def ingest(batch: SensorBatch) -> dict:
        result = ingestion.ingest(batch)
        if not result.accepted:
            raise HTTPException(status_code=403, detail=result.reason)
        bus.drain()
        pipeline.flush()
        bus.drain()
        return {"accepted": True, "reason": result.reason, "event_id": result.event_id}

    @app.post("/v1/simulate", tags=["demo"])
    def simulate(
        tenant_id: str = Query("dev"),
        user_id: str = Query("u_demo"),
    ) -> dict:
        """Generate and ingest a walk → drive → walk commute for a user."""
        batches = simulate_day(tenant_id=tenant_id, user_id=user_id)
        for batch in batches:
            _process(batch)
        return {
            "ingested_batches": len(batches),
            "segments": len(timeline.timeline(tenant_id, user_id)),
        }

    @app.get(
        "/v1/users/{user_id}/timeline",
        response_model=list[Segment],
        tags=["insights"],
    )
    def get_timeline(
        user_id: str,
        tenant_id: str = Query("dev"),
        since: float | None = Query(None),
        until: float | None = Query(None),
    ) -> list[Segment]:
        return timeline.timeline(tenant_id, user_id, since, until)

    @app.get("/v1/users/{user_id}/summary", tags=["insights"])
    def get_summary(
        user_id: str,
        tenant_id: str = Query("dev"),
        since: float | None = Query(None),
        until: float | None = Query(None),
    ) -> dict:
        return timeline.summary(tenant_id, user_id, since, until)

    return app


app = create_app()
