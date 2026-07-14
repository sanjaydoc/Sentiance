"""A small world for the mind to live in.

Instead of only reacting to text you type, the mind can inhabit a tiny simulated
place — rooms connected by exits, objects to notice, ambient events, and a
day/night clock. The world produces **stimuli** (what she perceives around her)
and accepts **actions** parsed from her own thoughts (moving between rooms,
examining things). This grounds her experience in a place she can sense and
affect, rather than in disembodied prompts.

Movement is intentional, not just literal: a thought that *names* a room, or
merely *implies* one ("time to make breakfast" → the kitchen; "I'll step outside"
→ the garden), is followed. Rooms that aren't adjacent are reached a step at a
time (she walks *toward* what she wants), so a wish forms a little journey.
"""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field

from sentiance.mind.state import Stimulus

_TIMES = ("dawn", "morning", "afternoon", "dusk", "night")

_MOVE_RE = re.compile(
    r"\b(?:go|move|walk|head|step|wander|come|make my way|set off)\s+"
    r"(?:to|into|toward|towards|through|out to|down to|back to|over to)?\s*"
    r"(?:the\s+)?([a-z][a-z ]*)",
    re.IGNORECASE,
)
_EXAMINE_RE = re.compile(
    r"\b(?:examine|look at|inspect|study|check)\s+(?:the\s+)?([a-z][a-z ]*)",
    re.IGNORECASE,
)

# What a room affords: words that express *wanting* what a room offers, so an
# intention ("I'm hungry", "I need some air") pulls her toward the right place
# even when she never names the room itself.
_AFFORDANCES: dict[str, set[str]] = {
    "kitchen": {
        "breakfast", "eat", "eating", "food", "hungry", "hunger", "meal", "cook",
        "cooking", "kettle", "tea", "coffee", "bread", "fruit", "snack", "drink",
        "kitchen",
    },
    "garden": {
        "outside", "garden", "air", "sky", "sun", "sunlight", "tree", "leaves",
        "wind", "stroll", "nature", "bench", "outdoors", "fresh",
    },
    "bedroom": {
        "rest", "sleep", "asleep", "nap", "bed", "tired", "curtains", "bedroom",
        "lie", "lay",
    },
    "hallway": {"clock", "photograph", "photo", "hall", "hallway", "corridor"},
}


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
    visited: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Count the room she wakes in as already seen once.
        self.visited.setdefault(self.current, 1)

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
        if place.exits:
            ways = " and ".join(place.exits)
            options.append((f"from the {place.name} a way leads to the {ways}", ["exit"]))
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

    # --- movement primitives ---------------------------------------------

    def _step(self, name: str) -> str:
        """Enter an *adjacent* room by exact name and record the visit."""
        self.current = name
        self.visited[name] = self.visited.get(name, 0) + 1
        return f"I step into the {name}."

    def _resolve_room(self, text: str) -> str | None:
        """Match free text against a known room name (either direction)."""
        text = text.strip().lower()
        if not text:
            return None
        for name in self.places:
            if name in text or text in name:
                return name
        return None

    def _path_to(self, dest: str) -> list[str]:
        """Shortest room path from the current place to ``dest`` (inclusive of
        both ends), or ``[]`` if unreachable. Breadth-first over the exits."""
        if dest not in self.places:
            return []
        prev: dict[str, str | None] = {self.current: None}
        queue: deque[str] = deque([self.current])
        while queue:
            node = queue.popleft()
            if node == dest:
                break
            for nb in self.places[node].exits:
                if nb not in prev:
                    prev[nb] = node
                    queue.append(nb)
        if dest not in prev:
            return []
        path = [dest]
        while path[-1] != self.current:
            path.append(prev[path[-1]])  # type: ignore[arg-type]
        path.reverse()
        return path

    def _go_toward(self, dest: str) -> str | None:
        """Take a single step along the shortest path toward ``dest``."""
        if dest == self.current:
            return None
        path = self._path_to(dest)
        if len(path) < 2:
            return None
        return self._step(path[1])

    def head_to(self, dest: str) -> str | None:
        """Take a single step along the shortest path toward ``dest`` (any room,
        not just an adjacent one). Public wrapper over the pathfinder."""
        return self._go_toward(dest)

    def _affordance_target(self, text: str) -> str | None:
        """Which room best satisfies what the thought is reaching for?"""
        words = set(re.findall(r"[a-z]+", text.lower()))
        best, best_score = None, 0
        for room, triggers in _AFFORDANCES.items():
            score = len(words & triggers)
            if score > best_score:
                best, best_score = room, score
        return best

    # --- public actions ---------------------------------------------------

    def move(self, target: str) -> str | None:
        """Move to a directly-adjacent room named ``target`` (one hop only)."""
        target = target.strip().lower()
        for name in self.here().exits:
            if name in target or target in name:
                return self._step(name)
        return None

    def examine(self, target: str) -> str | None:
        target = target.strip().lower()
        for obj in self.here().objects:
            if target in obj or any(w in obj for w in target.split()):
                return f"I look closely at {obj}."
        return None

    def drift(self) -> str | None:
        """Restlessness moves her along: step through the least-visited exit, so
        boredom becomes exploration rather than a stall. Returns the outcome."""
        exits = self.here().exits
        if not exits:
            return None
        target = min(exits, key=lambda n: (self.visited.get(n, 0), n))
        return self._step(target)

    def act(self, thought: str) -> str | None:
        """Try to carry out an action expressed in a thought. Returns an outcome
        description if something happened, else ``None``.

        Priority: an explicit "go to X" → a room named anywhere in the thought →
        an *implied* room (an affordance she's reaching for) → examining an object.
        Non-adjacent rooms are approached one step at a time.
        """
        # 1. An explicit movement verb with a destination.
        move = _MOVE_RE.search(thought)
        if move:
            dest = self._resolve_room(move.group(1))
            if dest:
                outcome = self._go_toward(dest)
                if outcome:
                    return outcome

        # 2. Any known room named anywhere in the thought.
        lowered = thought.lower()
        for name in self.places:
            if name != self.current and re.search(rf"\b{name}\b", lowered):
                outcome = self._go_toward(name)
                if outcome:
                    return outcome

        # 3. An implied destination — something she wants that a room provides.
        target = self._affordance_target(thought)
        if target and target != self.current:
            outcome = self._go_toward(target)
            if outcome:
                return outcome

        # 4. Examining something present here.
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
