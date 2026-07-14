"""Goals & intentions — the faculty that gives the mind agency.

A reactive stream only responds. This faculty lets the mind *form* an intention
(from an explicit thought like "I should check the noise", or from a strong
drive such as safety under threat or curiosity toward the novel), **hold** it
across ticks, let it bias attention and deliberation, and eventually **resolve**
it (when addressed or its drive is satisfied) or **abandon** it (when it goes
stale). Loosely a belief–desire–intention (BDI) layer over the drives.
"""

from __future__ import annotations

import re

from sentiance.mind.state import (
    AffectState,
    Appraisal,
    ConsciousMoment,
    Drive,
    Emotion,
    Goal,
    GoalStatus,
)
from sentiance.mind.util import clamp, tokenize

# "I should check the noise", "I need to find out", "I want to understand this"
_INTENTION_RE = re.compile(
    r"\bi (?:should|need to|want to|must|will|have to|ought to|mean to|ll)\s+(.+?)(?:[.!?]|$)",
    re.IGNORECASE,
)


class GoalSystem:
    def __init__(self, max_active: int = 3) -> None:
        self.goals: list[Goal] = []
        self.max_active = max_active

    def active(self) -> list[Goal]:
        return sorted(
            (g for g in self.goals if g.status is GoalStatus.ACTIVE),
            key=lambda g: g.urgency,
            reverse=True,
        )

    def descriptions(self) -> list[str]:
        return [g.description for g in self.active()]

    def top(self) -> Goal | None:
        active = self.active()
        return active[0] if active else None

    def update(
        self,
        moment: ConsciousMoment,
        appraisal: Appraisal,
        drive: Drive,
        affect: AffectState,
        drive_levels: dict[Drive, float],
    ) -> list[tuple[str, Goal]]:
        """Advance existing goals, then maybe form a new one. Returns
        ``(event, goal)`` pairs — event in {"formed", "resolved", "abandoned"} —
        so a UI can announce them."""
        events: list[tuple[str, Goal]] = []
        cue = set(tokenize(moment.content))

        for goal in self.active():
            goal.urgency = clamp(goal.urgency - 0.08)  # intentions fade if not fed
            # Safety goals are resolved by the drive recovering, not by words.
            if goal.drive is Drive.SAFETY and drive_levels.get(Drive.SAFETY, 1.0) >= 0.85:
                goal.progress = 1.0
            elif cue & set(tokenize(goal.description)):
                goal.progress = clamp(goal.progress + 0.5)
                goal.urgency = clamp(goal.urgency + 0.15)  # re-engaged
            goal.updated_tick = moment.tick

            if goal.progress >= 1.0:
                goal.status = GoalStatus.RESOLVED
                events.append(("resolved", goal))
            elif goal.urgency <= 0.08 and goal.progress < 0.5:
                goal.status = GoalStatus.ABANDONED
                events.append(("abandoned", goal))

        formed = self._maybe_form(moment, drive, affect, drive_levels)
        if formed is not None:
            events.append(("formed", formed))
        return events

    # --- formation --------------------------------------------------------

    def _maybe_form(
        self,
        moment: ConsciousMoment,
        drive: Drive,
        affect: AffectState,
        drive_levels: dict[Drive, float],
    ) -> Goal | None:
        if len(self.active()) >= self.max_active:
            return None

        desc: str | None = None
        goal_drive = drive
        urgency = 0.6

        # 1. An explicit intention voiced in the conscious content.
        match = _INTENTION_RE.search(moment.content)
        if match:
            desc = _clean(match.group(1))
        # 2. A threat with no standing safety goal.
        elif affect.emotion in (Emotion.FEAR, Emotion.ANGER) and not self._has_drive(Drive.SAFETY):
            desc, goal_drive, urgency = "restore a sense of safety", Drive.SAFETY, 0.85
        # 3. Something novel and intriguing worth understanding.
        elif affect.emotion in (Emotion.CURIOSITY, Emotion.SURPRISE):
            topic = _topic(moment.content)
            if topic:
                desc, goal_drive, urgency = f"understand {topic}", Drive.CURIOSITY, 0.65

        if not desc or self._duplicate(desc):
            return None

        goal = Goal(
            description=desc,
            drive=goal_drive,
            created_tick=moment.tick,
            updated_tick=moment.tick,
            urgency=urgency,
        )
        self.goals.append(goal)
        return goal

    def _has_drive(self, drive: Drive) -> bool:
        return any(g.drive is drive for g in self.active())

    def _duplicate(self, desc: str) -> bool:
        new = set(tokenize(desc))
        if not new:
            return True
        for g in self.active():
            existing = set(tokenize(g.description))
            if existing and len(new & existing) / len(new | existing) >= 0.6:
                return True
        return False

    # --- persistence ------------------------------------------------------

    def dump(self) -> dict:
        return {"goals": [g.model_dump() for g in self.goals]}

    def load(self, data: dict) -> None:
        self.goals = [Goal(**g) for g in data.get("goals", [])]


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().strip("\"'").rstrip(".")


def _topic(content: str) -> str:
    """A short noun-ish phrase to name a curiosity goal after."""
    words = tokenize(content)
    # Drop leading filler; keep the last couple of content words.
    kept = [w for w in words if w not in {"a", "an", "the", "some", "that", "this"}]
    return " ".join(kept[-3:]) if kept else ""
