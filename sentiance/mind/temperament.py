"""Temperament & needs — individuality and intrinsic wants.

**Temperament** is disposition — how curious, anxious, or optimistic this
particular mind is. It shapes *appraisal* (before feeling), so two minds meet the
same event and react differently: the anxious one feels a threat more keenly and
less in control; the optimistic one finds the same moment brighter; the curious
one is rewarded by novelty.

Disposition is stable but **not fixed**. Through :meth:`Temperament.drift`, lived
experience slowly reshapes the traits — an exponential moving average that lets
the *distribution* of what she goes through pull who she is: a life of warm,
controllable moments makes her more optimistic and less anxious; novelty that
keeps paying off deepens her curiosity; repeated fright she can't master makes
her warier. The plasticity is small on purpose — character shifts over a life, not
a moment — and the traits stay bounded, so she remains recognizably herself while
still being changed by what she lives. (A functional correlate of personality
plasticity; no claim that the change is *felt*.)

**Needs** are homeostatic pressures that build over time — rest, stimulation,
connection. Left unmet they weigh on how things feel (restlessness when
understimulated, a flatness when isolated), giving the mind intrinsic wants
rather than only reactions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sentiance.mind.state import Appraisal
from sentiance.mind.util import clamp


@dataclass
class Temperament:
    curiosity: float = 0.5  # appetite for novelty
    anxiety: float = 0.5  # threat sensitivity
    optimism: float = 0.5  # baseline positive lean
    plasticity: float = 0.01  # how readily experience reshapes the traits
    # The disposition she was born with — a fixed reference she drifts away from.
    innate: tuple[float, float, float] = field(default=(0.5, 0.5, 0.5))

    def __post_init__(self) -> None:
        # Unless explicitly given, her innate baseline is where she starts.
        if self.innate == (0.5, 0.5, 0.5):
            self.innate = (self.curiosity, self.anxiety, self.optimism)

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

    def drift(
        self, *, novelty: float, valence: float, arousal: float, control: float
    ) -> None:
        """Let one lived moment nudge the traits toward what experience implies.

        Each trait is an EMA that tracks the running tone of her life:
        - **optimism** follows how things generally turn out (valence);
        - **anxiety** rises with threat she can't control, falls with safety she
          can — weighted by how activating the moment is;
        - **curiosity** shifts only when she actually meets novelty, by whether
          that novelty rewards her or costs her.
        """
        a = self.plasticity

        self.optimism = _ema(self.optimism, clamp(0.5 + 0.5 * valence), a)

        threat = max(0.0, -valence) * (1.0 - control)
        safety = max(0.0, valence) * control
        anx_target = clamp(0.5 + 0.8 * threat - 0.6 * safety)
        self.anxiety = _ema(self.anxiety, anx_target, a * (0.5 + 0.5 * arousal))

        if novelty > 0.35:  # curiosity only learns from moments that were new
            self.curiosity = _ema(self.curiosity, clamp(0.5 + 0.5 * valence), a * novelty)

    def drift_from_innate(self) -> dict[str, float]:
        """How far each trait has been moved from where she began (signed)."""
        ic, ia, io = self.innate
        return {
            "curiosity": round(self.curiosity - ic, 3),
            "anxiety": round(self.anxiety - ia, 3),
            "optimism": round(self.optimism - io, 3),
        }

    def dump(self) -> dict:
        return {
            "curiosity": self.curiosity,
            "anxiety": self.anxiety,
            "optimism": self.optimism,
            "innate": list(self.innate),
        }

    def load(self, data: dict) -> None:
        self.curiosity = float(data.get("curiosity", self.curiosity))
        self.anxiety = float(data.get("anxiety", self.anxiety))
        self.optimism = float(data.get("optimism", self.optimism))
        innate = data.get("innate")
        if innate and len(innate) == 3:
            self.innate = (float(innate[0]), float(innate[1]), float(innate[2]))


def _ema(value: float, target: float, alpha: float) -> float:
    """Nudge ``value`` a small step toward ``target`` (stays in [0, 1])."""
    return clamp((1.0 - alpha) * value + alpha * target)


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
