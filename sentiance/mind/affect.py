"""Affect: turn an appraisal into feeling.

Feeling is represented dimensionally on Russell's circumplex — **valence**
(pleasant↔unpleasant) and **arousal** (calm↔activated) — and then labelled with a
discrete **emotion** using the appraisal (novelty, control). Acute affect blends
with the prior state (feelings have momentum), and a slow **mood** tracks the
running background via an exponential moving average.
"""

from __future__ import annotations

from sentiance.mind.state import AffectState, Appraisal, Emotion, Percept
from sentiance.mind.util import clamp


class AffectSystem:
    def __init__(self, mood_inertia: float = 0.9, emotion_decay: float = 0.6) -> None:
        self.mood_inertia = mood_inertia
        self.emotion_decay = emotion_decay

    def appraise(
        self, percept: Percept, appraisal: Appraisal, prev: AffectState
    ) -> AffectState:
        target_valence = clamp(appraisal.goal_congruence, -1.0, 1.0)
        target_arousal = clamp(
            0.35 * appraisal.novelty
            + 0.35 * percept.intensity * appraisal.relevance
            + 0.30 * abs(appraisal.goal_congruence)
        )

        # How forcefully this event moves the feeling (salient/relevant → more).
        influence = clamp(0.35 + 0.5 * appraisal.relevance + 0.15 * percept.novelty)

        valence = clamp(prev.valence * (1 - influence) + target_valence * influence, -1.0, 1.0)
        arousal = clamp(prev.arousal * (1 - influence) + target_arousal * influence)

        mood_valence = clamp(
            self.mood_inertia * prev.mood_valence + (1 - self.mood_inertia) * valence, -1.0, 1.0
        )
        mood_arousal = clamp(
            self.mood_inertia * prev.mood_arousal + (1 - self.mood_inertia) * arousal
        )

        return AffectState(
            valence=valence,
            arousal=arousal,
            emotion=self._label(valence, arousal, appraisal),
            mood_valence=mood_valence,
            mood_arousal=mood_arousal,
        )

    @staticmethod
    def _label(valence: float, arousal: float, appraisal: Appraisal) -> Emotion:
        # Novelty with unclear valence reads as surprise (hot) or curiosity (cool).
        if appraisal.novelty >= 0.6 and abs(valence) < 0.25:
            return Emotion.SURPRISE if arousal >= 0.6 else Emotion.CURIOSITY

        if valence >= 0.2:
            return Emotion.JOY if arousal >= 0.5 else Emotion.CONTENTMENT

        if valence <= -0.2:
            if arousal >= 0.5:
                # Low control over a bad, activating event → fear; high control → anger.
                return Emotion.FEAR if appraisal.control < 0.5 else Emotion.ANGER
            return Emotion.SADNESS

        # Ambiguous but activating and hard to make sense of → confusion.
        if appraisal.novelty >= 0.4 and appraisal.control < 0.45 and arousal >= 0.35:
            return Emotion.CONFUSION

        return Emotion.NEUTRAL
