"""Volition & self-control — holding focus against the pull of the moment.

Attention, on its own, is involuntary: the most salient thing wins, and the mind
is dragged wherever the loudest signal points. Volition is the top-down
counterweight — the capacity to *hold* attention on what she means to be doing
even when something flashier competes for it. It isn't free: exerting control
spends a limited reserve of **effort** that fatigues with use and recovers with
rest. So she can override a distraction while she has the willpower for it, and
when the reserve runs dry the impulse wins — she succumbs, as minds do.

A functional correlate of executive control / ego-depletion (Baumeister;
Posner's endogenous attention); no claim the effort is felt as effort.
"""

from __future__ import annotations

from dataclasses import dataclass

from sentiance.mind.state import Candidate
from sentiance.mind.util import clamp


@dataclass
class Volition:
    effort: float = 1.0  # the reserve of self-control she can spend
    recovery: float = 0.06  # how much it replenishes on a tick she doesn't exert
    max_boost: float = 0.6  # the most focus willpower can add at once

    def focus(self, candidates: list[Candidate], relevant: list[bool]) -> bool:
        """Try to keep a goal-relevant candidate in the spotlight when something
        else is out-competing it. Boosts its salience just enough to overtake,
        funded by (and depleting) the effort reserve. Mutates ``candidates`` in
        place; returns whether she actually exerted control this tick."""
        rel = [i for i, r in enumerate(relevant) if r]
        if not rel or self.effort < 0.1:
            self._recover()
            return False

        top_rel = max(rel, key=lambda i: candidates[i].salience)
        leader = max(range(len(candidates)), key=lambda i: candidates[i].salience)
        if leader == top_rel:
            self._recover()  # already focused — no willpower needed
            return False

        need = candidates[leader].salience - candidates[top_rel].salience + 0.02  # just past
        boost = min(self.max_boost, self.effort, need)
        candidates[top_rel] = candidates[top_rel].model_copy(
            update={"salience": clamp(candidates[top_rel].salience + boost)}
        )
        self.effort = clamp(self.effort - boost)
        return True

    def restore(self) -> None:
        """A night's rest returns her full capacity for self-control."""
        self.effort = 1.0

    def recover(self) -> None:
        """A tick spent not exerting control lets the reserve replenish a little."""
        self._recover()

    def _recover(self) -> None:
        self.effort = clamp(self.effort + self.recovery)

    def dump(self) -> dict:
        return {"effort": self.effort}

    def load(self, data: dict) -> None:
        self.effort = float(data.get("effort", 1.0))
