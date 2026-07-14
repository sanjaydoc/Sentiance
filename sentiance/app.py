"""HTTP runtime for a single living mind.

One process hosts one ``Mind``. You present stimuli, let it idle (wander), and
read its conscious moments, first-person reports, and self-model.
"""

from __future__ import annotations

from fastapi import FastAPI, Query

from sentiance import __version__
from sentiance.mind import Mind, Stimulus
from sentiance.mind.mind import TickResult
from sentiance.mind.state import SelfModelState


def create_app(mind: Mind | None = None) -> FastAPI:
    app = FastAPI(title="Sentiance — a mind", version=__version__)
    app.state.mind = mind or Mind()

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.post("/v1/perceive", response_model=TickResult, tags=["mind"])
    def perceive(stimulus: Stimulus) -> TickResult:
        """Present a stimulus; return what the mind became conscious of + its report."""
        return app.state.mind.perceive(stimulus)

    @app.post("/v1/idle", response_model=list[TickResult], tags=["mind"])
    def idle(ticks: int = Query(1, ge=1, le=100)) -> list[TickResult]:
        """Let the mind wander for N ticks with no external input."""
        return [app.state.mind.idle() for _ in range(ticks)]

    @app.get("/v1/self", response_model=SelfModelState, tags=["mind"])
    def self_state() -> SelfModelState:
        """The mind's current model of itself."""
        return app.state.mind.state()

    return app


app = create_app()
