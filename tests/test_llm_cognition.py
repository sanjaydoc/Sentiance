"""LLM-backed cognition — exercised with a fake client (no network, no keys)."""

from __future__ import annotations

from dataclasses import dataclass

from sentiance.core.config import Settings
from sentiance.mind import Mind, Stimulus
from sentiance.mind.cognition import LLMCognition, SimulatedCognition, build_cognition
from sentiance.mind.memory import Memory
from sentiance.mind.state import AffectState, ContentSource, Drive, Emotion, SelfModelState

# --- Fakes that mimic the Anthropic SDK response shape --------------------


@dataclass
class _Block:
    type: str
    text: str


@dataclass
class _Response:
    content: list
    stop_reason: str = "end_turn"


class _FakeMessages:
    def __init__(self, outer: _FakeClient) -> None:
        self._outer = outer

    def create(self, *, model, max_tokens, system, messages):  # noqa: ANN001
        self._outer.calls.append({"model": model, "system": system, "messages": messages})
        if self._outer.raise_error:
            raise RuntimeError("boom")
        return _Response(
            content=[_Block("text", self._outer.reply)],
            stop_reason=self._outer.stop_reason,
        )


class _FakeClient:
    def __init__(self, reply="I feel the pull of something new.", raise_error=False,
                 stop_reason="end_turn") -> None:
        self.reply = reply
        self.raise_error = raise_error
        self.stop_reason = stop_reason
        self.calls: list = []
        self.messages = _FakeMessages(self)


def _self_model() -> SelfModelState:
    return SelfModelState(
        name="Aria",
        tick=1,
        current_focus="a new idea",
        affect=AffectState(valence=0.4, arousal=0.6, emotion=Emotion.CURIOSITY),
        drives={Drive.CURIOSITY: 0.5},
        narrative="curiosity·a new idea",
    )


def test_llm_cognition_returns_thought_from_client() -> None:
    client = _FakeClient(reply="I want to trace where this idea leads.")
    cog = LLMCognition(client=client)
    result = cog.deliberate("a new idea", ContentSource.PERCEPT, _self_model(), Memory())

    assert isinstance(result, Stimulus)
    assert result.content == "I want to trace where this idea leads."
    assert result.source == "inner"
    # The prompt used Opus 4.8 and carried the affective state.
    assert client.calls[0]["model"] == "claude-opus-4-8"
    assert "arousal" in client.calls[0]["messages"][0]["content"]


def test_llm_cognition_falls_back_on_error() -> None:
    client = _FakeClient(raise_error=True)
    cog = LLMCognition(client=client, fallback=SimulatedCognition())
    sm = _self_model()  # curiosity → SimulatedCognition emits a "wonder" thought
    result = cog.deliberate("a new idea", ContentSource.PERCEPT, sm, Memory())
    assert result is not None
    assert "wonder" in result.content.lower()


def test_llm_cognition_falls_back_when_client_unavailable() -> None:
    # No client injected and (in CI) no anthropic/key → must degrade, not crash.
    cog = LLMCognition(fallback=SimulatedCognition())
    cog._client_failed = True  # simulate a failed lazy build
    result = cog.deliberate("a new idea", ContentSource.PERCEPT, _self_model(), Memory())
    assert result is not None  # came from the fallback


def test_refusal_is_treated_as_failure() -> None:
    client = _FakeClient(reply="", stop_reason="refusal")
    cog = LLMCognition(client=client, fallback=SimulatedCognition())
    result = cog.deliberate("a new idea", ContentSource.PERCEPT, _self_model(), Memory())
    # Refusal → fallback (curiosity thought), not an empty/None from the model.
    assert result is not None
    assert "wonder" in result.content.lower()


def test_build_cognition_selects_backend() -> None:
    assert isinstance(build_cognition(Settings(cognition_backend="simulated")), SimulatedCognition)
    assert isinstance(build_cognition(Settings(cognition_backend="llm")), LLMCognition)


def test_mind_runs_with_injected_llm_cognition() -> None:
    client = _FakeClient(reply="This is worth staying with.")
    mind = Mind(settings=Settings(), cognition=LLMCognition(client=client))
    # The inner thought produced at tick 1 becomes the stimulus wandered into next.
    mind.perceive(Stimulus(content="a warm light", intensity=0.6, tags=["light"]))
    r2 = mind.idle()
    assert r2.moment.content  # the mind kept thinking, fed by the LLM voice
    assert client.calls  # the model was consulted
