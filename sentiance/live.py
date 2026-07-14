"""Let the mind *live* in the small world — sense, feel, think, and act.

Each step: the world presents what she perceives, she reflects (one thought,
streamed if the backend supports it), and if that thought expresses an action
(moving to another room, examining something) the world carries it out and feeds
the outcome back. Run with ``python -m sentiance live``.
"""

from __future__ import annotations

from sentiance.chat import (
    _announce_curiosity,
    _announce_goals,
    _announce_self_judgment,
    format_tick,
)
from sentiance.mind import Mind
from sentiance.mind.state import Stimulus
from sentiance.world import World, default_home


def _place_stim(world: World, room: str) -> Stimulus:
    return Stimulus(
        content=f"I am in the {room} — {world.places[room].description}",
        source="imagined",
        intensity=0.5,
        tags=["place", "imagined"],
    )


def _consider_moving(mind: Mind, world: World, margin: float = 0.05) -> tuple[str, float] | None:
    """Imagine each way out *and* staying put, then move only if some room clearly
    beats staying. Curiosity makes the unexplored the most appealing future, so
    she keeps discovering — until everything is familiar and she settles."""
    exits = world.here().exits
    if not exits:
        return None
    options = [(room, _place_stim(world, room)) for room in exits]
    options.append(("stay", _place_stim(world, world.current)))
    ranked = mind.foresee(options)
    best = ranked[0]
    stay = next(p for p in ranked if p.option == "stay")
    if best.option == "stay" or best.appeal - stay.appeal < margin:
        return None  # nothing out there beckons more than where she is
    outcome = world.move(best.option)  # options are adjacent exits
    return (outcome, best.affect.valence) if outcome else None


class _Printer:
    """Streams tokens to stdout, indenting before the first one."""

    def __init__(self) -> None:
        self.any = False

    def __call__(self, chunk: str) -> None:
        if not self.any:
            print("  ", end="", flush=True)
            self.any = True
        print(chunk, end="", flush=True)


def run_live(mind: Mind | None = None, world: World | None = None, steps: int = 12) -> None:
    mind = mind or Mind()
    world = world or default_home()
    name = mind.settings.agent_name
    print(f"— {name} opens her eyes in the {world.current} (cognition: "
          f"{mind.settings.cognition_backend}) —\n")

    for _ in range(steps):
        world.tick()
        # 1. Perceive the surroundings.
        print(format_tick(mind.perceive(world.sense(), deliberate=False)))
        _announce_goals(mind)
        _announce_curiosity(mind)
        _announce_self_judgment(mind)

        # 2. Reflect — one thought (streamed live if the backend can).
        printer = _Printer()
        thought = mind.think(on_token=printer)
        if thought is None:
            continue
        if not printer.any:
            print(f"  {thought.content}", end="")
        print()
        mind.perceive(thought, deliberate=False)

        # 3. Act, if the thought expressed one — the world responds.
        before = world.current
        outcome = world.act(thought.content)
        if outcome:
            print(f"      → {outcome}")
            mind.perceive(
                Stimulus(content=outcome, source="world", intensity=0.5, tags=["action"]),
                deliberate=False,
            )

        # If her thought didn't move her, foresight still gets a say: curiosity
        # pulls her toward the room that promises the most to discover.
        if world.current == before:
            relocated = _consider_moving(mind, world)
            if relocated:
                outcome, imagined_v = relocated
                print(f"      → (foreseeing) {outcome}  [it felt like {imagined_v:+.2f}]")
                mind.perceive(
                    Stimulus(content=outcome, source="world", intensity=0.5, tags=["action"]),
                    deliberate=False,
                )

    print(f"\n— {name} rests. She is in the {world.current}. —")
