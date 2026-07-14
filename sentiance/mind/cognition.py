"""Cognition: deliberate action — what the mind does *with* a conscious moment.

Behind a stable ``Cognition`` port so the "thinking" engine is swappable
(ports & adapters). The reference ``SimulatedCognition`` is deterministic and
offline: from the current emotion and drives it forms the next inner thought,
which becomes a self-generated stimulus on the following tick — giving the mind a
self-sustaining inner stream. ``LLMCognition`` is the drop-in point for an
LLM-backed inner monologue and needs no change elsewhere.
"""

from __future__ import annotations

from typing import Protocol

from sentiance.mind.memory import Memory
from sentiance.mind.state import ContentSource, Emotion, SelfModelState, Stimulus


class Cognition(Protocol):
    """Decide the next self-generated inner content (or ``None`` to fall quiet)."""

    def deliberate(
        self, moment_content: str, source: ContentSource, self_model: SelfModelState, memory: Memory
    ) -> Stimulus | None:
        ...


class SimulatedCognition:
    """Template-based inner voice driven by emotion and drive state."""

    def deliberate(
        self, moment_content: str, source: ContentSource, self_model: SelfModelState, memory: Memory
    ) -> Stimulus | None:
        emotion = self_model.affect.emotion
        focus = self_model.current_focus

        if emotion in (Emotion.CURIOSITY, Emotion.SURPRISE):
            related = memory.associations(focus.split()[-1] if focus else "")
            hint = f" It reminds me of {related[0]}." if related else ""
            return Stimulus(
                content=f"I wonder what \"{focus}\" really means.{hint}",
                source="inner",
                intensity=0.4,
                tags=["question", "reflection"],
            )
        if emotion is Emotion.FEAR:
            return Stimulus(
                content=f"I should be careful about \"{focus}\".",
                source="inner",
                intensity=0.45,
                tags=["caution", "reflection"],
            )
        if emotion in (Emotion.JOY, Emotion.CONTENTMENT):
            return Stimulus(
                content=f"I'd like to stay with \"{focus}\" a little longer.",
                source="inner",
                intensity=0.3,
                tags=["desire", "reflection"],
                valence_hint=0.4,
            )
        if emotion is Emotion.SADNESS:
            return Stimulus(
                content=f"I keep returning to \"{focus}\".",
                source="inner",
                intensity=0.3,
                tags=["rumination", "reflection"],
                valence_hint=-0.3,
            )
        if emotion is Emotion.CONFUSION:
            return Stimulus(
                content=f"I'm trying to make sense of \"{focus}\".",
                source="inner",
                intensity=0.35,
                tags=["reflection"],
            )
        return None  # calm/neutral: let the mind fall quiet and wander


class LLMCognition:  # pragma: no cover - integration adapter
    """LLM-backed inner monologue (drop-in for ``SimulatedCognition``).

    Construct with a callable ``complete(prompt: str) -> str`` (e.g. a wrapper
    around the Anthropic client). Kept import-safe so the package runs offline.
    """

    def __init__(self, complete) -> None:  # noqa: ANN001 - user-supplied callable
        self._complete = complete

    def deliberate(
        self, moment_content: str, source: ContentSource, self_model: SelfModelState, memory: Memory
    ) -> Stimulus | None:
        prompt = (
            f"You are {self_model.name}, a mind reflecting privately.\n"
            f"You are attending to: {moment_content}\n"
            f"You feel {self_model.affect.emotion.value} "
            f"(valence {self_model.affect.valence:+.2f}).\n"
            f"Recent stream: {self_model.narrative}\n"
            "Write your next single private thought in the first person."
        )
        text = self._complete(prompt).strip()
        if not text:
            return None
        return Stimulus(content=text, source="inner", intensity=0.4, tags=["reflection"])
