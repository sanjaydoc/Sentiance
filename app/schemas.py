"""Pydantic request/response models for the API."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Sentiment(StrEnum):
    """Coarse sentiment label."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class AnalyzeRequest(BaseModel):
    """A single piece of text to analyze."""

    text: str = Field(..., min_length=1, max_length=10_000, examples=["I love this product!"])


class AnalyzeResponse(BaseModel):
    """The sentiment result for a piece of text."""

    text: str
    sentiment: Sentiment
    score: float = Field(..., ge=-1.0, le=1.0, description="Polarity in [-1.0, 1.0].")


class BatchAnalyzeRequest(BaseModel):
    """A batch of texts to analyze in one call."""

    texts: list[str] = Field(..., min_length=1, max_length=100)


class BatchAnalyzeResponse(BaseModel):
    """Results for a batch request."""

    results: list[AnalyzeResponse]


class HealthResponse(BaseModel):
    """Liveness/readiness payload."""

    status: str = "ok"
    app: str
    version: str
    environment: str
