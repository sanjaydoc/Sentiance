"""Intrinsic curiosity — an epistemic drive to reduce uncertainty.

Reward-seeking minds chase food and safety; a *sentient-seeming* one also chases
*understanding* for its own sake. This faculty gives Aria two things:

- **A draw toward the unknown.** When she imagines her options, the ones that
  would teach her most (high prediction error — the unexplored room, the
  unfamiliar sound) earn an appeal bonus, scaled by how *epistemically hungry*
  she is right now. This is active inference — acting to resolve uncertainty —
  and, as a side effect, it makes her finish exploring her world instead of
  circling the rooms she already knows.

- **The quiet reward of understanding.** Something that was, at first, surprising
  and then becomes familiar has been *understood*; that drop in surprise is
  intrinsically pleasant — a small "aha" that lifts her feeling and feeds the
  curiosity drive.

No claim of phenomenal wonder; this is the functional correlate — behaviour and
affect organised around information gain.
"""

from __future__ import annotations

from collections.abc import Callable

from sentiance.mind.state import Drive, Stimulus
from sentiance.mind.util import clamp, tokenize

_STOP = frozenset(
    {
        "a", "an", "the", "some", "that", "this", "i", "am", "is", "are", "in", "on",
        "it", "of", "to", "and", "my", "me", "here", "there", "with", "was", "were",
    }
)


def wonder_key(content: str) -> str:
    """A short key naming what a moment is 'about', for tracking curiosity."""
    toks = [t for t in tokenize(content) if t not in _STOP]
    return toks[-1] if toks else ""


class Curiosity:
    """Hunger to reduce uncertainty: draws her toward the informative, and rewards
    the moment the once-surprising becomes understood."""

    def __init__(self, weight: float = 0.6, wonder_span: int = 16) -> None:
        self.weight = weight
        self.wonder_span = wonder_span
        # Topics she has found surprising and not yet resolved: key -> first novelty.
        self._wondered: dict[str, float] = {}

    def hunger(self, drive_levels: dict[Drive, float]) -> float:
        """Epistemic appetite — high when the curiosity drive is unsatisfied."""
        return clamp(1.0 - drive_levels.get(Drive.CURIOSITY, 0.5))

    def appeal_bonus(
        self, drive_levels: dict[Drive, float]
    ) -> Callable[[Stimulus, float], float]:
        """A bonus function for imagination: reward expected information gain
        (novelty), amplified by her current epistemic hunger."""
        hunger = self.hunger(drive_levels)

        def bonus(_stimulus: Stimulus, novelty: float) -> float:
            return round(self.weight * novelty * (0.4 + 0.6 * hunger), 4)

        return bonus

    def observe(self, content: str, novelty: float) -> float:
        """Register the current moment. If it resolves a standing wonder (a topic
        that was surprising and is now familiar), return the 'aha' reward that
        should lift her feeling; otherwise note any fresh surprise and return 0."""
        key = wonder_key(content)
        if not key:
            return 0.0
        if key in self._wondered and novelty <= 0.35:
            first = self._wondered.pop(key)
            return round(clamp(0.4 * (first - novelty)), 4)  # understanding feels good
        if novelty >= 0.6:
            self._wondered.setdefault(key, novelty)
            while len(self._wondered) > self.wonder_span:
                self._wondered.pop(next(iter(self._wondered)))
        return 0.0

    # --- persistence ------------------------------------------------------

    def dump(self) -> dict:
        return {"wondered": dict(self._wondered)}

    def load(self, data: dict) -> None:
        self._wondered = {k: float(v) for k, v in data.get("wondered", {}).items()}
