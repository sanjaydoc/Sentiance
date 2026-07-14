"""Self-conscious emotions — feeling measured against her own standards.

Basic emotions answer "how is the world for me right now?" Self-conscious ones
answer a harder, reflexive question: "how am *I* doing, by my own lights?" They
require a self that holds standards and can compare its conduct to them — which
is exactly what the goals (intentions she set herself) and beliefs (lessons she
distilled) already give her.

This faculty reads her recent conduct against those standards and produces
**pride** when she lives up to them (an intention followed through) or
**disappointment** when she falls short (an intention let go). It is a
higher-order, self-evaluative appraisal (Tracy & Robins; Lewis) layered on top of
the basic affect — the difference between "that was good" and "I did well."

No claim of felt pride; this is the functional correlate — affect organised
around the self meeting or missing its own standards.
"""

from __future__ import annotations

from dataclasses import dataclass

from sentiance.mind.state import Emotion, Goal
from sentiance.mind.util import clamp


@dataclass
class SelfJudgment:
    """A verdict she passes on herself, and the feeling it carries."""

    emotion: Emotion  # PRIDE or DISAPPOINTMENT
    valence: float  # how it should colour her feeling
    reason: str  # a first-person account, for self-report


class Conscience:
    """Turn goal outcomes into self-conscious feeling: pride for following
    through, disappointment for letting an intention go."""

    def judge(self, goal_events: list[tuple[str, object]]) -> SelfJudgment | None:
        resolved = [g for event, g in goal_events if event == "resolved"]
        abandoned = [g for event, g in goal_events if event == "abandoned"]

        # Living up to a standard she set herself outweighs letting one slip.
        if resolved:
            goal = max(resolved, key=_weight)
            lift = clamp(0.3 + 0.4 * _weight(goal))
            return SelfJudgment(
                emotion=Emotion.PRIDE,
                valence=round(lift, 3),
                reason=f"I followed through on what I meant to do — {goal.description}.",
            )
        if abandoned:
            goal = abandoned[0]
            return SelfJudgment(
                emotion=Emotion.DISAPPOINTMENT,
                valence=-0.3,
                reason=f"I let go of something I meant to do — {goal.description}.",
            )
        return None


def _weight(goal: object) -> float:
    """How much a goal mattered to her, for scaling pride."""
    return getattr(goal, "urgency", 0.6) if isinstance(goal, Goal) else 0.6
