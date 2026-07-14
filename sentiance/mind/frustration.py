"""Frustration & anger — what a thwarted goal does to feeling and behaviour.

Fear withdraws; anger *approaches*. The difference is control: a bad, activating
event she feels helpless before reads as fear, but one she feels able to push
back on reads as anger. This faculty supplies the missing cause — **frustration**
that builds when an intention she holds keeps being blocked, and, once it crosses
a threshold, turns a bad blocked moment into **anger**: high arousal, still
unpleasant, but oriented toward *doing something about it*. It also fuels
persistence — anger re-charges the very goal that was being thwarted, so she digs
in rather than giving up.

A functional correlate of frustration→aggression (Berkowitz) and the
control/approach dimension of anger (appraisal theory); no claim it is felt.
"""

from __future__ import annotations

from dataclasses import dataclass

from sentiance.mind.util import clamp


@dataclass
class Frustration:
    level: float = 0.0
    threshold: float = 0.5  # above this, a blocked bad moment becomes anger
    build: float = 0.22  # how fast being thwarted stokes it
    cool: float = 0.12  # how fast it settles when nothing blocks her

    def update(self, *, has_goal: bool, goal_congruence: float) -> float:
        """One tick of pursuit: a held intention meeting a thwarting moment builds
        frustration; anything else lets it cool. Returns the new level."""
        if has_goal and goal_congruence < 0.0:
            self.level = clamp(self.level + self.build + 0.3 * (-goal_congruence))
        else:
            self.level = clamp(self.level - self.cool)
        return self.level

    def relieve(self, amount: float = 0.4) -> None:
        """Progress or resolution vents the pressure — the relief of getting through."""
        self.level = clamp(self.level - amount)

    @property
    def angry(self) -> bool:
        return self.level >= self.threshold

    def dump(self) -> dict:
        return {"level": self.level}

    def load(self, data: dict) -> None:
        self.level = float(data.get("level", 0.0))
