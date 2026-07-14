"""A society — several minds sharing one small world, meeting and socializing.

No two minds are wired together. They simply *inhabit the same house*: each has
its own body (a position among the rooms) and its own private stream. When two of
them end up in the same room they **perceive each other** as ``@Name`` — which is
exactly what the relationship, attachment, empathy and grief faculties already
speak. So everything social is emergent:

- they **meet** (a first co-presence becomes a warm handshake),
- they **talk** (each one's inner thought is voiced to whoever is present, carrying
  how they feel — so the listener catches it, via empathy),
- they **bond** (repeated warm company deepens attachment),
- they **seek company** when lonely and **miss** each other once apart.

Nothing here reaches inside another mind; the only channel between them is the
shared world and the words they say in it — just like people.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from sentiance.mind import Mind
from sentiance.mind.state import AffectState, Emotion, Stimulus
from sentiance.world import World, default_home

# How a felt emotion shows on the outside — chosen so the *watcher's* empathy
# (which reads these very words) can catch it.
_EXPRESSION: dict[Emotion, str] = {
    Emotion.JOY: "beaming",
    Emotion.CONTENTMENT: "smiling",
    Emotion.CURIOSITY: "smiling",
    Emotion.FEAR: "trembling",
    Emotion.ANGER: "furious",
    Emotion.SADNESS: "sad",
    Emotion.GRIEF: "grieving",
    Emotion.HOPE: "smiling",
    Emotion.DREAD: "trembling",
}


@dataclass
class Inhabitant:
    """One mind living in the shared house, with its own position and voice."""

    name: str
    mind: Mind
    world: World  # its own body/position over the *shared* rooms
    last_utterance: str | None = None
    last_emotion: Emotion = Emotion.NEUTRAL
    was_with: set[str] = field(default_factory=set)

    @property
    def room(self) -> str:
        return self.world.current


def _express(emotion: Emotion) -> str | None:
    return _EXPRESSION.get(emotion)


def _social_stimulus(other: Inhabitant, *, first_meeting: bool) -> Stimulus:
    """What it's like, this moment, to be with ``other`` — a handshake on meeting,
    otherwise hearing what they just said (coloured by how they seem to feel)."""
    if first_meeting:
        return Stimulus(
            content=f"@{other.name} and I meet — we share a warm handshake",
            source="world", intensity=0.6, tags=["social", "friend", "warmth"],
        )
    show = _express(other.last_emotion)
    if other.last_utterance:
        seems = f", {show}," if show else ""
        return Stimulus(
            content=f"@{other.name}{seems} says: {other.last_utterance}",
            source="world", intensity=0.55, tags=["social", "friend"],
        )
    seems = f" (they seem {show})" if show else ""
    return Stimulus(
        content=f"@{other.name} is here beside me{seems}",
        source="world", intensity=0.5, tags=["social", "friend"],
    )


class Society:
    def __init__(self, inhabitants: list[Inhabitant]) -> None:
        self.inhabitants = inhabitants

    def occupants(self, room: str, exclude: str) -> list[Inhabitant]:
        return [i for i in self.inhabitants if i.name != exclude and i.room == room]

    def _nearest_occupied(self, me: Inhabitant) -> str | None:
        """The closest room (by the house's layout) that holds someone else."""
        occupied = {i.room for i in self.inhabitants if i.name != me.name}
        best, best_len = None, 1_000_000
        for room in occupied:
            path = me.world._path_to(room)  # noqa: SLF001 - same package
            if path and 1 < len(path) < best_len:
                best, best_len = room, len(path)
        return best

    def step(self) -> list[tuple[Inhabitant, AffectState, str, list[str]]]:
        """Advance every inhabitant one moment. Returns per-inhabitant
        (who, how-they-felt, what-they-perceived, [social notes]) for display."""
        transcript: list[tuple[Inhabitant, AffectState, str, list[str]]] = []
        for me in self.inhabitants:
            others = self.occupants(me.room, me.name)
            here = {o.name for o in others}

            if others:
                other = others[0]
                first = other.name not in me.was_with
                stim = _social_stimulus(other, first_meeting=first)
            else:
                stim = me.world.sense()
            me.was_with = here

            # 1. Perceive the moment (meeting / hearing another / the room), and
            #    capture the reaction *now* — before her own next thought overwrites
            #    the per-tick social signals (empathy, longing).
            me.mind.perceive(stim, deliberate=False)
            social_affect = me.mind.affect
            me.last_emotion = social_affect.emotion
            notes = self._note_social(me, others, me.mind.last_empathy, me.mind.longing)

            # 2. Say the next thought (voiced to whoever is here), then live it.
            thought = me.mind.think()
            me.last_utterance = thought.content if thought is not None else None
            if thought is not None:
                me.mind.perceive(thought, deliberate=False)

            self._move(me, thought.content if thought else "", others)
            transcript.append((me, social_affect, stim.content, notes))
        return transcript

    def _note_social(
        self,
        me: Inhabitant,
        others: list[Inhabitant],
        empathy: tuple[str, float] | None,
        longing: tuple[str, float] | None,
    ) -> list[str]:
        notes: list[str] = []
        for other in others:
            rel = me.mind.relationships.known(other.name)
            if rel is not None:
                bond = ("bonded" if rel.attachment >= 0.6
                        else "close" if rel.attachment >= 0.3 else "acquainted")
                notes.append(f"with @{other.name} ({bond}, affection {rel.affection:+.2f})")
        if empathy is not None:
            notes.append(f"catches @{empathy[0]}'s feeling")
        if longing is not None:
            notes.append(f"misses @{longing[0]}")
        return notes

    def _move(self, me: Inhabitant, thought: str, others: list[Inhabitant]) -> None:
        # With company she tends to stay unless her thought says otherwise; alone
        # and lonely, she goes looking for someone.
        before = me.room
        me.world.act(thought)
        if me.room != before:
            return
        if not others and me.mind.needs.connection < 0.5:
            target = self._nearest_occupied(me)
            if target:
                me.world.head_to(target)


def _cast() -> list[Inhabitant]:
    """Three housemates with distinctly different natures."""
    from sentiance.core.config import Settings

    places = default_home().places
    specs = [
        ("Iris", {"temperament_curiosity": 0.9, "temperament_optimism": 0.8,
                  "temperament_anxiety": 0.2}, "bedroom"),
        ("Milo", {"temperament_curiosity": 0.4, "temperament_optimism": 0.3,
                  "temperament_anxiety": 0.85}, "kitchen"),
        ("Rhea", {"temperament_curiosity": 0.6, "temperament_optimism": 0.6,
                  "temperament_anxiety": 0.4}, "garden"),
    ]
    people: list[Inhabitant] = []
    for name, traits, room in specs:
        mind = Mind(settings=Settings(agent_name=name, **traits))
        # Each body has its own position, but the rooms themselves are shared.
        people.append(Inhabitant(name=name, mind=mind,
                                 world=World(places=places, current=room)))
    return people


def run_society(
    inhabitants: list[Inhabitant] | None = None,
    steps: int = 24,
    persist: bool = True,
    emit: Callable[[str], None] = print,
) -> Society:
    from sentiance.chat import default_persist_path  # noqa: PLC0415 - avoid cycle

    people = inhabitants or _cast()
    society = Society(people)

    if persist:
        for i in people:
            recovered = i.mind.load(default_persist_path(i.mind.settings))
            if recovered:
                emit(f"  …{i.name} remembers {recovered} moments from before.")

    names = ", ".join(f"{i.name} in the {i.room}" for i in people)
    backend = people[0].mind.settings.cognition_backend
    emit(f"— a house wakes: {names} (cognition: {backend}) —\n")

    def _remember() -> None:
        if persist:
            for i in people:
                i.mind.save(default_persist_path(i.mind.settings))

    # Save as we go (and on interrupt), so a long or halted run never loses their
    # bonds — the memory files appear after the first few moments, not only at the end.
    try:
        for tick in range(steps):
            for me, affect, perceived, notes in society.step():
                emit(f"  [{me.name} @ {me.room}] {perceived}")
                emit(f"      [{affect.emotion.value} v{affect.valence:+.2f}]"
                     + (f"  ·  {'; '.join(notes)}" if notes else ""))
                if me.last_utterance:
                    emit(f"      {me.name}: {me.last_utterance}")
            emit("")
            if (tick + 1) % 4 == 0:
                _remember()  # checkpoint their memories periodically
    except KeyboardInterrupt:
        emit("\n  (left early)")
    finally:
        _remember()
        if persist:
            emit("— the house sleeps; each remembers the others —")
    return society
