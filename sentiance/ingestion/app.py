"""FastAPI ingestion gateway.

Authenticates the caller (API key → tenant), then delegates to
``IngestionService``. The API-key resolver is pluggable; the default dev
resolver accepts a configured key. In production this maps keys to tenants and
rejects mismatched ``tenant_id`` in the payload.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, FastAPI, Header, HTTPException

from sentiance import __version__
from sentiance.core.bus.base import EventBus
from sentiance.core.schemas import SensorBatch
from sentiance.ingestion.service import IngestionService

TenantResolver = Callable[[str], str | None]


def dev_tenant_resolver(api_key: str) -> str | None:
    """Accept a single dev key; the tenant travels in the payload for demos."""
    return "dev" if api_key == "dev-key" else None


def create_ingestion_app(
    bus: EventBus,
    service: IngestionService | None = None,
    tenant_resolver: TenantResolver = dev_tenant_resolver,
) -> FastAPI:
    app = FastAPI(title="Sentiance Ingestion Gateway", version=__version__)
    svc = service or IngestionService(bus)

    def require_tenant(x_api_key: str = Header(...)) -> str:
        tenant = tenant_resolver(x_api_key)
        if tenant is None:
            raise HTTPException(status_code=401, detail="invalid API key")
        return tenant

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.post("/v1/batches", tags=["ingestion"])
    def ingest_batch(batch: SensorBatch, _tenant: str = Depends(require_tenant)) -> dict:
        result = svc.ingest(batch)
        if not result.accepted:
            raise HTTPException(status_code=403, detail=result.reason)
        return {
            "accepted": True,
            "reason": result.reason,
            "event_id": result.event_id,
        }

    return app


def _build_default_app() -> FastAPI:
    """Module-level ASGI app wired from settings (used by uvicorn / compose)."""
    from sentiance.core.config import get_settings
    from sentiance.core.wiring import build_bus

    return create_ingestion_app(build_bus(get_settings()))


app = _build_default_app()
