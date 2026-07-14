"""A small world for the mind to live in.

Instead of only reacting to text you type, the mind can inhabit a tiny simulated
place — rooms connected by exits, objects to notice, ambient events, and a
day/night clock. The world produces **stimuli** (what she perceives around her)
and accepts **actions** parsed from her own thoughts (moving between rooms,
examining things). This grounds her experience in a place she can sense and
affect, rather than in disembodied prompts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from sentiance.mind.state import Stimulus

_TIMES = ("dawn", "morning", "afternoon", "dusk", "night")

_MOVE_RE = re.compile(
    r"\b(?:go|move|walk|head|step|wander)\s+(?:to|into|toward|towards|through|out to|down to)?\s*"
    r"(?:the\s+)?([a-z][a-z ]*)",
    re.IGNORECASE,
)
_EXAMINE_RE = re.compile(
    r"\b(?:examine|look at|inspect|study|check)\s+(?:the\s+)?([a-z][a-z ]*)",
    re.IGNORECASE,
)


@dataclass
class Place:
    name: str
    description: str
    exits: list[str] = field(default_factory=list)  # names of adjacent places
    objects: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)  # ambient things that happen here


@dataclass
class World:
    places: dict[str, Place]
    current: str
    clock: int = 0

    def here(self) -> Place:
        return self.places[self.current]

    def time_of_day(self) -> str:
        return _TIMES[(self.clock // 4) % len(_TIMES)]

    def tick(self) -> None:
        self.clock += 1

    def sense(self) -> Stimulus:
        """Return what the mind notices in the current place this moment."""
        place = self.here()
        options: list[tuple[str, list[str]]] = [
            (f"{self.time_of_day()} light fills the {place.name}", ["light", self.time_of_day()]),
            (f"I am in the {place.name} — {place.description}", ["place"]),
        ]
        if place.objects:
            obj = place.objects[self.clock % len(place.objects)]
            options.append((f"there is {obj} here", ["object"]))
        if place.events:
            ev = place.events[self.clock % len(place.events)]
            options.append((ev, ["event"]))
        content, tags = options[self.clock % len(options)]
        return Stimulus(content=content, source="world", intensity=0.5, tags=tags)

    def exits_text(self) -> str:
        return ", ".join(self.here().exits) or "(nowhere)"

    def move(self, target: str) -> str | None:
        target = target.strip().lower()
        for name in self.here().exits:
            if name in target or target in name:
                self.current = name
                return f"I step into the {name}."
        return None

    def examine(self, target: str) -> str | None:
        target = target.strip().lower()
        for obj in self.here().objects:
            if target in obj or any(w in obj for w in target.split()):
                return f"I look closely at {obj}."
        return None

    def act(self, thought: str) -> str | None:
        """Try to carry out an action expressed in a thought. Returns an outcome
        description if something happened, else ``None``."""
        move = _MOVE_RE.search(thought)
        if move:
            outcome = self.move(move.group(1))
            if outcome:
                return outcome
        examine = _EXAMINE_RE.search(thought)
        if examine:
            return self.examine(examine.group(1))
        return None


def default_home() -> World:
    """A small house + garden the mind can wander through."""
    places = {
        "bedroom": Place(
            "bedroom",
            "a quiet room with a bed and a curtained window",
            exits=["hallway"],
            objects=["a soft bed", "a window with pale curtains"],
            events=["a bird sings somewhere outside the window"],
        ),
        "hallway": Place(
            "hallway",
            "a narrow hallway with a wooden floor",
            exits=["bedroom", "kitchen", "garden"],
            objects=["a framed photograph", "an old clock"],
            events=["the house creaks quietly", "the clock ticks"],
        ),
        "kitchen": Place(
            "kitchen",
            "a warm kitchen that smells faintly of bread",
            exits=["hallway"],
            objects=["a copper kettle", "a bowl of fruit"],
            events=["the kettle ticks as it cools"],
        ),
        "garden": Place(
            "garden",
            "an open garden under a wide sky",
            exits=["hallway"],
            objects=["a tall oak tree", "a weathered stone bench"],
            events=["wind moves through the leaves", "a distant dog barks once"],
        ),
    }
    return World(places=places, current="bedroom")
