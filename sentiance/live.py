"""Let the mind *live* in the small world — sense, feel, think, and act.

Each step: the world presents what she perceives, she reflects (one thought,
streamed if the backend supports it), and if that thought expresses an action
(moving to another room, examining something) the world carries it out and feeds
the outcome back. Run with ``python -m sentiance live``.
"""

from __future__ import annotations

from sentiance.chat import _announce_goals, format_tick
from sentiance.mind import Mind
from sentiance.mind.state import Stimulus
from sentiance.world import World, default_home


def _relocate_by_foresight(mind: Mind, world: World) -> tuple[str, float] | None:
    """When nothing else moves her, imagine each way out and walk toward the most
    appealing room — foresight, not a blind shuffle. Returns (outcome, valence)."""
    exits = world.here().exits
    if not exits:
        return None
    options = [
        (
            room,
            Stimulus(
                content=f"I am in the {room} — {world.places[room].description}",
                source="imagined",
                intensity=0.5,
                tags=["place", "imagined"],
            ),
        )
        for room in exits
    ]
    best = mind.foresee(options)[0]
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

        # If her thought didn't move her but she's grown restless (stimulation
        # low), she imagines the ways out and walks toward the most appealing.
        if world.current == before and mind.needs.stimulation < 0.5:
            relocated = _relocate_by_foresight(mind, world)
            if relocated:
                outcome, imagined_v = relocated
                print(f"      → (foreseeing) {outcome}  [it felt like {imagined_v:+.2f}]")
                mind.perceive(
                    Stimulus(content=outcome, source="world", intensity=0.5, tags=["action"]),
                    deliberate=False,
                )

    print(f"\n— {name} rests. She is in the {world.current}. —")
