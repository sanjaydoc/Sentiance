"""FastAPI application factory and ASGI entry point."""

from __future__ import annotations

from fastapi import FastAPI

from app import __version__
from app.config import get_settings
from app.routes import router


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="A FastAPI service for text sentiment analysis.",
    )
    app.include_router(router)

    @app.get("/", tags=["system"])
    def root() -> dict[str, str]:
        return {"service": settings.app_name, "docs": "/docs"}

    return app


app = create_app()
