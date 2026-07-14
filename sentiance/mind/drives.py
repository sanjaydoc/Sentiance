"""Intrinsic drives and appraisal — what the mind cares about, and how events
stand relative to those cares.

Drives are homeostatic: each has a satisfaction level that decays toward a
setpoint and is nudged by events. Appraisal (Scherer/OCC) reads an event against
the drives to produce the dimensions — novelty, goal-congruence, control,
relevance — that the affect system turns into feeling.
"""

from __future__ import annotations

from sentiance.mind.state import Appraisal, Drive, Percept
from sentiance.mind.util import clamp

_THREAT_TAGS = frozenset({"threat", "danger", "pain", "loss", "attack", "alarm"})
_PLEASANT_TAGS = frozenset({"reward", "praise", "play", "beauty", "success", "warmth"})
_SOCIAL_TAGS = frozenset({"person", "friend", "someone", "social", "voice", "you"})


class Drives:
    def __init__(self) -> None:
        # 1.0 = fully satisfied, 0.0 = urgent need.
        self.levels: dict[Drive, float] = {
            Drive.CURIOSITY: 0.5,
            Drive.COHERENCE: 0.7,
            Drive.SAFETY: 0.9,
            Drive.CONNECTION: 0.5,
        }
        self._setpoints: dict[Drive, float] = {
            Drive.CURIOSITY: 0.5,
            Drive.COHERENCE: 0.7,
            Drive.SAFETY: 0.9,
            Drive.CONNECTION: 0.5,
        }

    def appraise(self, percept: Percept) -> tuple[Appraisal, Drive]:
        tags = {t.lower() for t in percept.tags}
        threat = percept.intensity if tags & _THREAT_TAGS else 0.0
        pleasant = tags & _PLEASANT_TAGS
        social = tags & _SOCIAL_TAGS
        novelty = percept.novelty

        # Per-drive goal-congruence contributions and how relevant each is.
        contributions: dict[Drive, float] = {
            # Novelty feeds curiosity (a want that is *satisfied* by the new).
            Drive.CURIOSITY: novelty * (0.5 + 0.5 * (1 - self.levels[Drive.CURIOSITY])),
            # ...but novelty *costs* coherence (the world just got less predictable).
            Drive.COHERENCE: (0.5 - novelty),
            # Threat thwarts safety.
            Drive.SAFETY: -threat,
            # Social pleasant contact serves connection.
            Drive.CONNECTION: (0.6 if social else 0.0) + (0.3 if pleasant else 0.0),
        }

        dominant = max(contributions, key=lambda d: abs(contributions[d]))
        goal_congruence = clamp(contributions[dominant], -1.0, 1.0)
        # Carry a felt-valence hint (e.g. from a self-generated thought) into the
        # appraisal, so the mind's own reflection keeps the colour of its mood
        # instead of resetting to neutral each tick.
        if percept.valence_hint is not None:
            goal_congruence = clamp(0.6 * goal_congruence + 0.4 * percept.valence_hint, -1.0, 1.0)
        relevance = clamp(max(abs(v) for v in contributions.values()))
        control = clamp(0.75 - 0.6 * threat + 0.15 * self.levels[Drive.SAFETY] - 0.3 * novelty)

        self._apply(contributions, novelty, threat)
        return (
            Appraisal(
                novelty=novelty,
                goal_congruence=goal_congruence,
                control=control,
                relevance=relevance,
            ),
            dominant,
        )

    def decay(self, rate: float = 0.05) -> None:
        """Relax every drive toward its setpoint (homeostasis)."""
        for drive, setpoint in self._setpoints.items():
            self.levels[drive] += (setpoint - self.levels[drive]) * rate

    def dump(self) -> dict:
        return {drive.value: level for drive, level in self.levels.items()}

    def load(self, data: dict) -> None:
        for key, level in data.items():
            self.levels[Drive(key)] = float(level)

    # --- internals --------------------------------------------------------

    def _apply(self, contributions: dict[Drive, float], novelty: float, threat: float) -> None:
        # Curiosity is satisfied by novelty; coherence eroded by it; safety by threat.
        self.levels[Drive.CURIOSITY] = clamp(self.levels[Drive.CURIOSITY] + 0.4 * novelty)
        self.levels[Drive.COHERENCE] = clamp(self.levels[Drive.COHERENCE] - 0.3 * novelty)
        self.levels[Drive.SAFETY] = clamp(self.levels[Drive.SAFETY] - 0.5 * threat)
        if contributions[Drive.CONNECTION] > 0:
            self.levels[Drive.CONNECTION] = clamp(
                self.levels[Drive.CONNECTION] + 0.3 * contributions[Drive.CONNECTION]
            )
