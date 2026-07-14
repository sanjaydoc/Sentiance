"""FastAPI insights API — per-user timeline and daily summary reads."""

from __future__ import annotations

from fastapi import FastAPI, Query

from sentiance import __version__
from sentiance.core.schemas import Segment
from sentiance.insights.service import TimelineService


def create_insights_app(timeline_service: TimelineService) -> FastAPI:
    app = FastAPI(title="Sentiance Insights API", version=__version__)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get(
        "/v1/users/{user_id}/timeline",
        response_model=list[Segment],
        tags=["insights"],
    )
    def timeline(
        user_id: str,
        tenant_id: str = Query("dev"),
        since: float | None = Query(None),
        until: float | None = Query(None),
    ) -> list[Segment]:
        return timeline_service.timeline(tenant_id, user_id, since, until)

    @app.get("/v1/users/{user_id}/summary", tags=["insights"])
    def summary(
        user_id: str,
        tenant_id: str = Query("dev"),
        since: float | None = Query(None),
        until: float | None = Query(None),
    ) -> dict:
        return timeline_service.summary(tenant_id, user_id, since, until)

    return app


def _build_default_app() -> FastAPI:  # pragma: no cover - production wiring path
    """Module-level ASGI app (used by uvicorn / compose).

    Reads segments off the bus into the repository via a background consumer.
    In production the repository is the Postgres adapter; here it is in-memory,
    which is sufficient as a running reference of the serving topology.
    """
    import threading
    from contextlib import asynccontextmanager

    from sentiance.core.config import get_settings
    from sentiance.core.repositories.memory import InMemorySegmentRepository
    from sentiance.core.schemas import TOPIC_SEGMENT, Segment
    from sentiance.core.wiring import build_bus
    from sentiance.insights.service import SegmentConsumer

    settings = get_settings()
    repo = InMemorySegmentRepository()
    service = TimelineService(repo)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if settings.bus_backend == "kafka":
            bus = build_bus(
                settings,
                decoders={TOPIC_SEGMENT: lambda b: Segment.model_validate_json(b)},
            )
            SegmentConsumer(repo).register(bus)
            thread = threading.Thread(target=bus.run_forever, daemon=True)
            thread.start()
        yield

    built = create_insights_app(service)
    built.router.lifespan_context = lifespan
    return built


app = _build_default_app()
