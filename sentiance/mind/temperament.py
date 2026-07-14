"""Temperament & needs — individuality and intrinsic wants.

**Temperament** is stable disposition — how curious, anxious, or optimistic this
particular mind is. It shapes *appraisal* (before feeling), so two minds meet the
same event and react differently: the anxious one feels a threat more keenly and
less in control; the optimistic one finds the same moment brighter; the curious
one is rewarded by novelty.

**Needs** are homeostatic pressures that build over time — rest, stimulation,
connection. Left unmet they weigh on how things feel (restlessness when
understimulated, a flatness when isolated), giving the mind intrinsic wants
rather than only reactions.
"""

from __future__ import annotations

from dataclasses import dataclass

from sentiance.mind.state import Appraisal
from sentiance.mind.util import clamp


@dataclass
class Temperament:
    curiosity: float = 0.5  # appetite for novelty
    anxiety: float = 0.5  # threat sensitivity
    optimism: float = 0.5  # baseline positive lean

    def shape(self, appraisal: Appraisal) -> Appraisal:
        """Bias an appraisal by disposition, before it becomes feeling."""
        gc = appraisal.goal_congruence + (self.optimism - 0.5) * 0.3
        if appraisal.goal_congruence < 0:  # anxiety deepens the bad
            gc += (self.anxiety - 0.5) * -0.4
        gc += (self.curiosity - 0.5) * 0.3 * appraisal.novelty  # curiosity rewards the new
        control = clamp(appraisal.control - (self.anxiety - 0.5) * 0.4)
        return appraisal.model_copy(
            update={"goal_congruence": clamp(gc, -1.0, 1.0), "control": control}
        )


@dataclass
class Needs:
    rest: float = 0.7
    stimulation: float = 0.6
    connection: float = 0.6

    def step(self, novelty: float, arousal: float, social: bool, valence: float) -> None:
        """Deplete and replenish needs for one moment of living."""
        # Understimulation (low novelty) breeds boredom; the novel refreshes.
        self.stimulation = clamp(self.stimulation - 0.03 + 0.45 * novelty)
        # Connection fades without warm company.
        self.connection = clamp(
            self.connection - 0.04 + (0.35 if social and valence > 0 else 0.0)
        )
        # Activity (arousal) is tiring.
        self.rest = clamp(self.rest - 0.06 * arousal)

    def rest_now(self) -> None:
        self.rest = clamp(self.rest + 0.5)

    def pressure(self) -> float:
        """Negative valence pressure from unmet needs (0 when all are satisfied)."""
        deficit = sum(max(0.0, 0.35 - n) for n in (self.rest, self.stimulation, self.connection))
        return -deficit

    def most_pressing(self) -> str | None:
        low = {"rest": self.rest, "stimulation": self.stimulation, "connection": self.connection}
        name = min(low, key=low.get)
        return name if low[name] < 0.35 else None

    def dump(self) -> dict:
        return {"rest": self.rest, "stimulation": self.stimulation, "connection": self.connection}

    def load(self, data: dict) -> None:
        self.rest = float(data.get("rest", self.rest))
        self.stimulation = float(data.get("stimulation", self.stimulation))
        self.connection = float(data.get("connection", self.connection))
