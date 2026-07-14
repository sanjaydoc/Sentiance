"""HTTP routes for the sentiment API."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.config import get_settings
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    BatchAnalyzeRequest,
    BatchAnalyzeResponse,
    HealthResponse,
)
from app.sentiment import analyzer

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    """Report service liveness and basic metadata."""
    settings = get_settings()
    return HealthResponse(
        app=settings.app_name,
        version=__version__,
        environment=settings.environment,
    )


@router.post("/analyze", response_model=AnalyzeResponse, tags=["sentiment"])
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    """Analyze the sentiment of a single piece of text."""
    return analyzer.analyze(payload.text)


@router.post("/analyze/batch", response_model=BatchAnalyzeResponse, tags=["sentiment"])
def analyze_batch(payload: BatchAnalyzeRequest) -> BatchAnalyzeResponse:
    """Analyze the sentiment of several texts in one request."""
    return BatchAnalyzeResponse(
        results=[analyzer.analyze(text) for text in payload.texts],
    )
