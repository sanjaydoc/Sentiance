"""Trace export — turn a mind's living into a training dataset (Path A/B).

Set ``SENTIANCE_TRACE_PATH=data/traces.jsonl`` and every deliberation the mind
makes — in ``demo``, ``chat``, ``live``, or ``society`` — is appended as one JSON
line capturing exactly what the cognition saw and what it produced:

    {"agent", "system", "prompt", "thought",
     "state": {emotion, valence, arousal, drives, goals, heard, signals, source, focus},
     "state_vec": [...]}

- ``prompt`` / ``thought`` are a ready **supervised (input → output) pair** for
  fine-tuning a small model to speak in-character (Path A — the voice).
- ``state`` is the human-readable inner context of that same moment.
- ``state_vec`` is the whole cognitive cycle as a fixed-length numeric vector
  ``m_t`` (``state_vector.encode_state``) — the differentiable input the **fused**
  mind trains on (Path B — a cognition-conditioned transformer, ADR 0005).

Nothing changes about how the mind runs; tracing is a transparent wrapper around
the ``Cognition`` port (ADR-0003), so the model call is captured without touching
the cognitive cycle. The file is line-delimited JSON — stream it, shuffle it,
split it, or convert it to any chat-fine-tuning format.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from sentiance.mind.cognition import Cognition, OnToken, _compose_prompt
from sentiance.mind.state_vector import encode_state

if TYPE_CHECKING:
    from sentiance.mind.memory import Memory
    from sentiance.mind.state import ContentSource, SelfModelState, Stimulus


class TraceWriter:
    """Append-only JSONL sink, flushed per row so long runs stream to disk."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("a", encoding="utf-8")
        self.count = 0

    def write(self, record: dict) -> None:
        self._file.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._file.flush()
        self.count += 1

    def close(self) -> None:
        self._file.close()


# One shared writer per path, so several minds (a society) append to one file
# through a single handle rather than clobbering each other.
_WRITERS: dict[str, TraceWriter] = {}


def _writer_for(path: str) -> TraceWriter:
    writer = _WRITERS.get(path)
    if writer is None:
        writer = TraceWriter(path)
        _WRITERS[path] = writer
    return writer


class TracingCognition:
    """Wrap a ``Cognition`` and log each ``(prompt, state) → thought`` it makes."""

    def __init__(self, inner: Cognition, writer: TraceWriter) -> None:
        self.inner = inner
        self.writer = writer

    def deliberate(
        self,
        moment_content: str,
        source: ContentSource,
        self_model: SelfModelState,
        memory: Memory,
        on_token: OnToken | None = None,
    ) -> Stimulus | None:
        thought = self.inner.deliberate(moment_content, source, self_model, memory, on_token)
        if thought is not None:
            system, user = _compose_prompt(self_model, moment_content, source)
            affect = self_model.affect
            self.writer.write(
                {
                    "agent": self_model.name,
                    "system": system,
                    "prompt": user,
                    "thought": thought.content,
                    "state": {
                        "focus": moment_content,
                        "source": source.value,
                        "emotion": affect.emotion.value,
                        "valence": round(affect.valence, 3),
                        "arousal": round(affect.arousal, 3),
                        "mood_valence": round(affect.mood_valence, 3),
                        "drives": {d.value: round(v, 3) for d, v in self_model.drives.items()},
                        "goals": list(self_model.goals),
                        "heard": self_model.heard,
                        "signals": dict(self_model.signals),
                    },
                    # The whole cycle as one numeric vector — the differentiable
                    # input the fused, cognition-conditioned transformer trains on
                    # (state_vector.encode_state / ADR 0005). Path A ignores it;
                    # Path B/the fused mind consumes it.
                    "state_vec": [round(x, 4) for x in encode_state(self_model, source)],
                }
            )
        return thought


def wrap_with_trace(inner: Cognition, path: str) -> Cognition:
    """Return ``inner`` wrapped so its deliberations stream to the trace file."""
    return TracingCognition(inner, _writer_for(path))
