"""Relationships & theory-of-mind — persistent models of other people.

A person named in an experience with ``@Name`` (e.g. "@Sam greets me warmly") is
someone the mind can *know*. It keeps a per-person model — how many times they've
met, how she feels about them (affection), how much she trusts them — updated by
how each encounter felt. A known person then colors her appraisal *before*
anything happens: seeing a warm friend feels good on sight; a person who has hurt
her puts her on edge. This makes her socially continuous, not just
self-continuous.
"""

from __future__ import annotations

import re

from sentiance.mind.state import Relationship
from sentiance.mind.util import clamp

_PERSON_RE = re.compile(r"@(\w+)")


def extract_people(text: str) -> list[str]:
    """Names mentioned as ``@Name`` (order-preserving, de-duplicated)."""
    return list(dict.fromkeys(_PERSON_RE.findall(text)))


class RelationshipSystem:
    def __init__(self) -> None:
        self.people: dict[str, Relationship] = {}

    def known(self, name: str) -> Relationship | None:
        return self.people.get(name)

    def prior(self, names: list[str]) -> float | None:
        """Average affection toward the known people present, or None if strangers."""
        vals = [self.people[n].affection for n in names if n in self.people]
        return sum(vals) / len(vals) if vals else None

    def record(self, names: list[str], valence: float, tick: int) -> None:
        """Fold how this encounter felt into each person's model."""
        for name in names:
            rel = self.people.get(name)
            if rel is None:
                rel = Relationship(name=name, first_tick=tick)
                self.people[name] = rel
            rel.encounters += 1
            rel.affection = clamp(0.6 * rel.affection + 0.4 * valence, -1.0, 1.0)
            rel.trust = clamp(rel.trust + 0.08 * valence)
            rel.last_tick = tick

    def summary(self) -> list[str]:
        lines: list[str] = []
        for rel in sorted(self.people.values(), key=lambda r: r.encounters, reverse=True):
            tone = "warm" if rel.affection > 0.2 else "wary" if rel.affection < -0.2 else "neutral"
            lines.append(
                f"{rel.name}: {tone} (affection {rel.affection:+.2f}, "
                f"trust {rel.trust:.2f}, met {rel.encounters}x)"
            )
        return lines

    def dump(self) -> dict:
        return {"people": {n: r.model_dump() for n, r in self.people.items()}}

    def load(self, data: dict) -> None:
        self.people = {n: Relationship(**r) for n, r in data.get("people", {}).items()}
