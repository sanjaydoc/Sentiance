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


# Rotated deterministically by tick so the inner voice doesn't sound identical
# every moment (variety without randomness — reports stay reproducible/testable).
_OPENERS = (
    'I am aware that I am attending to {src} — "{c}".',
    'My attention settles on {src} — "{c}".',
    'I notice {src}: "{c}".',
    'It is {src} that holds me now — "{c}".',
)
_FEELINGS = (
    "I feel {e} (valence {v:+.2f}, arousal {a:.2f}).",
    "There is {e} in me — valence {v:+.2f}, arousal {a:.2f}.",
    "What rises is {e} ({v:+.2f} / {a:.2f}).",
)
_VERBS_POS = ("it answers", "it feeds", "it speaks to", "it serves")
_VERBS_NEG = ("it works against", "it unsettles", "it strains", "it presses on")
_VERBS_NEUTRAL = ("it brushes against", "it touches on", "it stirs", "it circles")


class Metacognition:
    def reflect(
        self,
        moment: ConsciousMoment,
        self_model: SelfModelState,
        appraisal: Appraisal,
        dominant_drive: Drive,
    ) -> IntrospectiveReport:
        affect = moment.affect
        i = max(0, moment.tick - 1)  # tick 1 → index 0 keeps "I am aware …" first
        source = _SOURCE_PHRASE[moment.source]

        opener = _OPENERS[i % len(_OPENERS)].format(src=source, c=moment.content)
        feeling = _FEELINGS[i % len(_FEELINGS)].format(
            e=affect.emotion.value, v=affect.valence, a=affect.arousal
        )
        reason = self._reason(appraisal, dominant_drive, i)
        text = f"{opener} {feeling} {reason}"
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
    def _reason(appraisal: Appraisal, drive: Drive, i: int) -> str:
        phrase = _DRIVE_PHRASE[drive]
        if appraisal.goal_congruence > 0.15:
            stance = f"{_VERBS_POS[i % len(_VERBS_POS)]} {phrase}"
        elif appraisal.goal_congruence < -0.15:
            stance = f"{_VERBS_NEG[i % len(_VERBS_NEG)]} {phrase}"
        else:
            stance = f"{_VERBS_NEUTRAL[i % len(_VERBS_NEUTRAL)]} {phrase}"

        # Novelty decays as themes recur, so the mind increasingly recognizes them.
        if appraisal.novelty >= 0.6:
            return f"This is new to me, and {stance}."
        if appraisal.novelty <= 0.3:
            return f"This feels familiar by now, and {stance}."
        return f"{stance[0].upper()}{stance[1:]}."
