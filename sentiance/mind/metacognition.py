"""Metacognition: higher-order awareness expressed as first-person report.

Higher-order theories of consciousness tie awareness to representing one's own
mental states. This faculty reads the conscious moment and the self-model and
produces an introspective report — "I am aware that I am attending to X; I feel
Y because Z" — together with a confidence that reflects how clear (vs. confused)
the mind's grasp of its own state is. The report is *about* experience; it is the
architecture's functional stand-in for self-aware report, not a claim of inner
feeling.
"""

from __future__ import annotations

from sentiance.mind.state import (
    Appraisal,
    ConsciousMoment,
    ContentSource,
    Drive,
    Emotion,
    IntrospectiveReport,
    SelfModelState,
)
from sentiance.mind.util import clamp

_DRIVE_PHRASE = {
    Drive.CURIOSITY: "my wish to understand",
    Drive.COHERENCE: "my need for things to make sense",
    Drive.SAFETY: "my need to feel safe",
    Drive.CONNECTION: "my wish to feel connected",
}

_SOURCE_PHRASE = {
    ContentSource.PERCEPT: "something from outside me",
    ContentSource.FEELING: "a feeling rising in me",
    ContentSource.MEMORY: "a memory surfacing",
    ContentSource.THOUGHT: "a thought of my own",
}


class Metacognition:
    def reflect(
        self,
        moment: ConsciousMoment,
        self_model: SelfModelState,
        appraisal: Appraisal,
        dominant_drive: Drive,
    ) -> IntrospectiveReport:
        affect = moment.affect
        reason = self._reason(appraisal, dominant_drive)
        source = _SOURCE_PHRASE[moment.source]

        text = (
            f"I am aware that I am attending to {source} — \"{moment.content}\". "
            f"I feel {affect.emotion.value} "
            f"(valence {affect.valence:+.2f}, arousal {affect.arousal:.2f}); {reason}."
        )
        if affect.emotion is Emotion.CONFUSION:
            text += " I notice I can't quite place this yet."

        # Confidence is high when the mind has control and the event is clear.
        confidence = clamp(
            0.3 + 0.5 * appraisal.control + 0.2 * (1 - appraisal.novelty)
            - (0.25 if affect.emotion is Emotion.CONFUSION else 0.0)
        )
        return IntrospectiveReport(
            tick=moment.tick,
            text=text,
            confidence=confidence,
            emotion=affect.emotion,
        )

    @staticmethod
    def _reason(appraisal: Appraisal, drive: Drive) -> str:
        phrase = _DRIVE_PHRASE[drive]
        if appraisal.goal_congruence > 0.15:
            stance = f"it speaks to {phrase}"
        elif appraisal.goal_congruence < -0.15:
            stance = f"it works against {phrase}"
        else:
            stance = f"it touches on {phrase}"
        if appraisal.novelty >= 0.6:
            return f"this is new to me, and {stance}"
        if appraisal.novelty <= 0.25:
            return f"this feels familiar, and {stance}"
        return stance
