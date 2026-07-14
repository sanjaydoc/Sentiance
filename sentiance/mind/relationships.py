"""Relationships & theory-of-mind — persistent models of other people.

A person named in an experience with ``@Name`` (e.g. "@Sam greets me warmly") is
someone the mind can *know*. It keeps a per-person model — how many times they've
met, how she feels about them (affection), how much she trusts them — updated by
how each encounter felt. A known person then colors her appraisal *before*
anything happens: seeing a warm friend feels good on sight; a person who has hurt
her puts her on edge. This makes her socially continuous, not just
self-continuous.

Beyond momentary affection, warmth repeated over time builds **attachment** — a
slow, sticky bond. A person she is attached to lifts her simply by being near, and
their long **absence is missed**: a longing that grows with the depth of the bond
and the time apart, draining her need for connection. Attachment is what makes
affection into something more like love — and what makes loss cost something.
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
            # Warmth deepens the bond (slowing as it grows); real hurt erodes it a little.
            if valence > 0:
                rel.attachment = clamp(rel.attachment + 0.06 * valence * (1 - 0.5 * rel.attachment))
            elif valence < -0.3:
                rel.attachment = clamp(rel.attachment + 0.04 * valence)
            rel.last_tick = tick

    def bond(self, names: list[str]) -> float:
        """The strongest attachment among the people present (0 if none/strangers)."""
        vals = [self.people[n].attachment for n in names if n in self.people]
        return max(vals) if vals else 0.0

    def missing(
        self, current_tick: int, present: set[str], min_absence: int = 5, full_at: int = 40
    ) -> tuple[str, float] | None:
        """Whom she most misses right now: someone she's attached to, absent a
        while. Returns ``(name, longing)`` — longing scales with the depth of the
        bond and how long they've been gone — or ``None`` if no one is missed."""
        best: tuple[str, float] | None = None
        for rel in self.people.values():
            if rel.name in present or rel.attachment < 0.2 or rel.lost:
                continue
            gap = current_tick - rel.last_tick
            if gap < min_absence:
                continue
            longing = clamp(rel.attachment * min(1.0, gap / full_at))
            if best is None or longing > best[1]:
                best = (rel.name, round(longing, 3))
        return best

    def summary(self) -> list[str]:
        lines: list[str] = []
        for rel in sorted(self.people.values(), key=lambda r: r.encounters, reverse=True):
            tone = "warm" if rel.affection > 0.2 else "wary" if rel.affection < -0.2 else "neutral"
            bond = (
                " — bonded" if rel.attachment >= 0.6
                else " — close" if rel.attachment >= 0.3
                else ""
            )
            lines.append(
                f"{rel.name}: {tone}{bond} (affection {rel.affection:+.2f}, "
                f"trust {rel.trust:.2f}, attachment {rel.attachment:.2f}, met {rel.encounters}x)"
            )
        return lines

    def dump(self) -> dict:
        return {"people": {n: r.model_dump() for n, r in self.people.items()}}

    def load(self, data: dict) -> None:
        self.people = {n: Relationship(**r) for n, r in data.get("people", {}).items()}
