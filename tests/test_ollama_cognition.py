"""Local (Ollama) cognition — exercised with a fake HTTP client (no server)."""

from __future__ import annotations

from dataclasses import dataclass, field

from sentiance.core.config import Settings
from sentiance.mind import Mind, Stimulus
from sentiance.mind.cognition import OllamaCognition, SimulatedCognition, build_cognition
from sentiance.mind.memory import Memory
from sentiance.mind.state import AffectState, ContentSource, Drive, Emotion, SelfModelState

# --- A fake mimicking httpx.Client against Ollama's /api/chat -------------


@dataclass
class _FakeResponse:
    payload: dict

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


class _FakeStream:
    """Context manager mimicking httpx's streaming response for /api/chat."""

    def __init__(self, chunks: list[str]) -> None:
        self._chunks = chunks

    def __enter__(self) -> _FakeStream:
        return self

    def __exit__(self, *exc) -> None:
        return None

    def raise_for_status(self) -> None:
        return None

    def iter_lines(self):
        import json as _json

        for c in self._chunks:  # deltas include their spacing, like real Ollama
            yield _json.dumps({"message": {"content": c}, "done": False})
        yield _json.dumps({"message": {"content": ""}, "done": True})


@dataclass
class _FakeHttp:
    content: str = "I turn the new thing over in my mind."
    raise_error: bool = False
    calls: list = field(default_factory=list)

    def post(self, url, json):  # noqa: A002 - match httpx signature
        self.calls.append({"url": url, "json": json})
        if self.raise_error:
            raise ConnectionError("connection refused")
        return _FakeResponse({"message": {"role": "assistant", "content": self.content}})

    def stream(self, method, url, json):  # noqa: A002 - match httpx signature
        self.calls.append({"method": method, "url": url, "json": json, "stream": True})
        if self.raise_error:
            raise ConnectionError("connection refused")
        import re

        return _FakeStream(re.findall(r"\S+\s*", self.content))  # keep spacing in deltas


def _self_model() -> SelfModelState:
    return SelfModelState(
        name="Aria",
        tick=1,
        current_focus="a new idea",
        affect=AffectState(valence=0.4, arousal=0.6, emotion=Emotion.CURIOSITY),
        drives={Drive.CURIOSITY: 0.5},
        narrative="curiosity·a new idea",
    )


def test_ollama_returns_thought_and_calls_chat_endpoint() -> None:
    http = _FakeHttp(content="I want to see where this leads.")
    cog = OllamaCognition(model="qwen2.5:7b", client=http)
    result = cog.deliberate("a new idea", ContentSource.PERCEPT, _self_model(), Memory())

    assert isinstance(result, Stimulus)
    assert result.content == "I want to see where this leads."
    assert result.source == "inner"
    # Hit Ollama's native chat endpoint with the configured model + affect prompt.
    assert http.calls[0]["url"] == "/api/chat"
    assert http.calls[0]["json"]["model"] == "qwen2.5:7b"
    assert http.calls[0]["json"]["stream"] is False
    assert "arousal" in http.calls[0]["json"]["messages"][1]["content"]


def test_ollama_falls_back_when_server_unreachable() -> None:
    http = _FakeHttp(raise_error=True)
    cog = OllamaCognition(client=http, fallback=SimulatedCognition())
    result = cog.deliberate("a new idea", ContentSource.PERCEPT, _self_model(), Memory())
    # Curiosity → simulated voice emits a "wonder" thought instead of crashing.
    assert result is not None
    assert "wonder" in result.content.lower()


def test_ollama_empty_response_falls_quiet() -> None:
    cog = OllamaCognition(client=_FakeHttp(content="   "))
    result = cog.deliberate("a new idea", ContentSource.PERCEPT, _self_model(), Memory())
    assert result is None


def test_build_cognition_selects_ollama() -> None:
    cog = build_cognition(Settings(cognition_backend="ollama", ollama_model="qwen2.5:7b"))
    assert isinstance(cog, OllamaCognition)
    assert cog.model == "qwen2.5:7b"


def test_mind_runs_with_injected_ollama_cognition() -> None:
    http = _FakeHttp(content="This is worth dwelling on.")
    mind = Mind(settings=Settings(), cognition=OllamaCognition(client=http))
    mind.perceive(Stimulus(content="a warm light", intensity=0.6, tags=["light"]))
    r2 = mind.idle()
    assert r2.moment.content
    assert http.calls  # the local model was consulted


def test_ollama_streams_tokens_when_on_token_given() -> None:
    http = _FakeHttp(content="one two three")
    cog = OllamaCognition(client=http)
    tokens: list[str] = []
    result = cog.deliberate(
        "a new idea", ContentSource.PERCEPT, _self_model(), Memory(), on_token=tokens.append
    )
    # Streamed word-by-word via /api/chat with stream=True, then assembled.
    assert len(tokens) == 3
    assert result.content == "one two three"
    assert http.calls[0]["json"]["stream"] is True


def test_mind_think_streams_and_perceive_does_not_double_generate() -> None:
    http = _FakeHttp(content="a quiet realization dawns")
    mind = Mind(settings=Settings(), cognition=OllamaCognition(client=http))
    mind.perceive(Stimulus(content="a warm light", intensity=0.6, tags=["light"]), deliberate=False)

    tokens: list[str] = []
    thought = mind.think(on_token=tokens.append)
    assert tokens  # the thought streamed live
    assert thought is not None
    # Feeding it back with deliberate=False must NOT trigger another model call.
    before = len(http.calls)
    mind.perceive(thought, deliberate=False)
    assert len(http.calls) == before
