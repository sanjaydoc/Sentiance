"""The self-model — the mind's internal model of itself.

Attention Schema Theory holds that a system reports being conscious because it
builds a simplified model of its own attention and reads that model out. This
faculty maintains exactly that: what the mind is currently attending to, how it
feels, the state of its drives, and a running autobiographical narrative — the
substrate every first-person report is generated from.
"""

from __future__ import annotations

from collections import deque

from sentiance.mind.state import (
    AffectState,
    ConsciousMoment,
    Drive,
    SelfModelState,
)


class SelfModel:
    def __init__(self, name: str, narrative_span: int = 6, belief_span: int = 12) -> None:
        self.name = name
        self.tick = 0
        self.current_focus = "(nothing yet)"
        self.affect = AffectState()
        self.drives: dict[Drive, float] = {}
        self._history: deque[str] = deque(maxlen=narrative_span)
        # Durable lessons distilled from experience during consolidation ("sleep").
        self._beliefs: deque[str] = deque(maxlen=belief_span)

    def add_beliefs(self, beliefs: list[str]) -> list[str]:
        """Add new beliefs (dedup against those already held). Returns the added."""
        added: list[str] = []
        existing = set(self._beliefs)
        for belief in beliefs:
            if belief not in existing:
                self._beliefs.append(belief)
                existing.add(belief)
                added.append(belief)
        return added

    @property
    def beliefs(self) -> list[str]:
        return list(self._beliefs)

    def update(self, moment: ConsciousMoment, drives: dict[Drive, float]) -> None:
        self.tick = moment.tick
        self.current_focus = moment.attention_target
        self.affect = moment.affect
        self.drives = dict(drives)
        self._history.append(f"{moment.affect.emotion.value}·{moment.content}")

    @property
    def narrative(self) -> str:
        return " → ".join(self._history) if self._history else "(no history yet)"

    def dump(self) -> dict:
        return {
            "tick": self.tick,
            "current_focus": self.current_focus,
            "history": list(self._history),
            "beliefs": list(self._beliefs),
            "affect": self.affect.model_dump(),
        }

    def load(self, data: dict) -> None:
        self.tick = int(data.get("tick", 0))
        self.current_focus = data.get("current_focus", self.current_focus)
        self._history = deque(data.get("history", []), maxlen=self._history.maxlen)
        self._beliefs = deque(data.get("beliefs", []), maxlen=self._beliefs.maxlen)
        if "affect" in data:
            self.affect = AffectState(**data["affect"])

    def snapshot(self) -> SelfModelState:
        return SelfModelState(
            name=self.name,
            tick=self.tick,
            current_focus=self.current_focus,
            affect=self.affect,
            drives=dict(self.drives),
            narrative=self.narrative,
            beliefs=self.beliefs,
        )
