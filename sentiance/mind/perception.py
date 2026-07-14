"""Perception: encode a stimulus into a percept with novelty and salience.

Bottom-up salience combines how *intense* a stimulus is with how *novel* it is
(prediction error from the world-model). This is the raw, pre-attentive pull a
stimulus exerts before affect and drives weigh in.
"""

from __future__ import annotations

from sentiance.mind.state import Percept, Stimulus
from sentiance.mind.util import clamp
from sentiance.mind.world_model import WorldModel


class Perceptor:
    def perceive(self, stimulus: Stimulus, world: WorldModel) -> Percept:
        novelty = world.surprise(stimulus.content, stimulus.tags)
        salience = clamp(0.45 * stimulus.intensity + 0.55 * novelty)
        return Percept(
            content=stimulus.content,
            tags=stimulus.tags,
            intensity=stimulus.intensity,
            novelty=novelty,
            salience=salience,
            valence_hint=stimulus.valence_hint,
            internal=stimulus.source == "inner",
        )
