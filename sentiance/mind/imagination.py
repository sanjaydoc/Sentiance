"""Imagination & foresight — prospection, the mind's forward model.

A mind that only reacts is blind to consequences. This faculty lets the mind
*pre-live* candidate next moments: for each option it runs the very same
perception → appraisal → affect machinery it uses for real experience, but as a
**dry run on copies that mutate nothing** — no memory laid down, no drive moved.
It reads off how each imagined moment *would* feel, and ranks the options by their
appeal, so the mind can choose the future it anticipates liking best.

This is mental time-travel in the spirit of predictive-processing forward models
(Friston/Clark, Schacter's constructive episodic simulation). No claim is made
that she *pictures* anything; this is the functional correlate — evaluating
hypotheticals by their anticipated affect before committing to one.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sentiance.mind.affect import AffectSystem
from sentiance.mind.drives import Drives
from sentiance.mind.perception import Perceptor
from sentiance.mind.state import AffectState, Stimulus
from sentiance.mind.temperament import Temperament
from sentiance.mind.world_model import WorldModel

# An extra pull a prospect may earn beyond how pleasant it feels (e.g. the draw
# of the unknown). Given (stimulus, novelty) → bonus. Curiosity supplies one.
AppealBonus = Callable[[Stimulus, float], float]


@dataclass
class Prospect:
    """One imagined future: an option, what she pictures happening, how it would
    feel, and how novel it would be."""

    option: str  # a short label for the choice (e.g. "the kitchen")
    imagined: str  # the hypothetical she pre-lived
    affect: AffectState  # how that moment would feel
    novelty: float
    bonus: float = 0.0  # extra pull (e.g. epistemic draw of the unknown)

    @property
    def appeal(self) -> float:
        """What draws her toward this future: mostly how pleasant it would feel,
        plus a gentle pull toward the novel, plus any external bonus."""
        return round(self.affect.valence + 0.15 * self.novelty + self.bonus, 4)


class Imagination:
    """Pre-live hypothetical moments without living them (a pure forward model)."""

    def __init__(
        self,
        perceptor: Perceptor,
        drives: Drives,
        affect_system: AffectSystem,
        temperament: Temperament,
    ) -> None:
        self.perceptor = perceptor
        self.drives = drives
        self.affect_system = affect_system
        self.temperament = temperament

    def foresee(
        self, stimulus: Stimulus, world: WorldModel, prior_affect: AffectState
    ) -> tuple[AffectState, float]:
        """Imagine how ``stimulus`` would feel *without living it*: run perception
        and appraisal on read-only state, mutating nothing. Returns the
        anticipated affect and the imagined moment's novelty."""
        percept = self.perceptor.perceive(stimulus, world)  # read-only novelty
        appraisal, _ = self.drives.evaluate(percept)  # pure — no homeostasis
        appraisal = self.temperament.shape(appraisal)
        anticipated = self.affect_system.appraise(percept, appraisal, prior_affect)
        return anticipated, percept.novelty

    def imagine(
        self,
        options: list[tuple[str, Stimulus]],
        world: WorldModel,
        prior_affect: AffectState,
        bonus: AppealBonus | None = None,
    ) -> list[Prospect]:
        """Pre-live each ``(label, hypothetical)`` option and return the prospects
        sorted by appeal, most appealing first. ``bonus`` adds an optional extra
        pull per option (e.g. the epistemic draw of the unfamiliar)."""
        prospects: list[Prospect] = []
        for label, stim in options:
            affect, novelty = self.foresee(stim, world, prior_affect)
            extra = bonus(stim, novelty) if bonus is not None else 0.0
            prospects.append(
                Prospect(
                    option=label,
                    imagined=stim.content,
                    affect=affect,
                    novelty=novelty,
                    bonus=round(extra, 4),
                )
            )
        return sorted(prospects, key=lambda p: p.appeal, reverse=True)
