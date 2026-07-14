"""The small world — sensing, moving, examining, and living in it."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.live import run_live
from sentiance.mind import Mind
from sentiance.world import World, default_home


def test_sense_produces_stimuli_about_the_current_place() -> None:
    w = default_home()
    seen = set()
    for _ in range(8):
        w.tick()
        s = w.sense()
        assert s.source == "world"
        seen.add(s.content)
    assert len(seen) > 1  # she notices different things over time
    assert any("bedroom" in c for c in seen)  # grounded in where she is


def test_time_of_day_cycles() -> None:
    w = default_home()
    times = set()
    for _ in range(20):
        w.tick()
        times.add(w.time_of_day())
    assert len(times) >= 3  # dawn/day/dusk/night all come around


def test_move_between_connected_rooms() -> None:
    w = default_home()  # starts in bedroom
    assert w.move("kitchen") is None  # not directly reachable from the bedroom
    assert w.move("hallway") is not None
    assert w.current == "hallway"
    assert w.move("garden") is not None
    assert w.current == "garden"


def test_act_parses_movement_and_examination_from_a_thought() -> None:
    w = default_home()
    assert w.act("I think I'll walk to the hallway now.") is not None
    assert w.current == "hallway"
    # Examine an object that's present here.
    assert w.act("let me look at the old clock") is not None
    # An action with no valid target does nothing.
    assert w.act("I wonder about the meaning of it all") is None


def test_run_live_drives_the_mind_through_the_world() -> None:
    mind = Mind(settings=Settings())  # simulated backend — offline
    world = World(places=default_home().places, current="bedroom")
    run_live(mind, world, steps=4)
    assert mind.tick_no >= 4  # she lived several moments
    # She perceived her surroundings (bedroom appears in her memory).
    assert any("bedroom" in t.content for t in mind.memory.episodic)
