"""Imagination & foresight — pre-living hypothetical moments (prospection)."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind
from sentiance.mind.state import Stimulus


def _stim(content: str, **kw: object) -> Stimulus:
    return Stimulus(content=content, intensity=0.6, **kw)  # type: ignore[arg-type]


def test_foreseeing_mutates_nothing() -> None:
    mind = Mind(settings=Settings())
    # Give the world-model and drives some state to notice a change against.
    mind.perceive(_stim("a warm friend greets me", tags=["friend"]))
    drives_before = dict(mind.drives.levels)
    world_before = mind.world.dump()
    affect_before = mind.affect.model_copy()

    prospects = mind.foresee(
        [
            ("a threat", _stim("a sudden violent attack", tags=["threat", "alarm"])),
            ("a delight", _stim("a burst of warm praise", tags=["reward", "praise"])),
        ]
    )

    assert len(prospects) == 2
    # Imagining the future changed none of her actual state.
    assert dict(mind.drives.levels) == drives_before
    assert mind.world.dump() == world_before
    assert mind.affect == affect_before


def test_a_pleasant_future_outranks_a_threatening_one() -> None:
    mind = Mind(settings=Settings())
    # Make both futures familiar first, so it's their *valence* being weighed,
    # not the raw novelty of a blank world (where everything is equally new).
    for _ in range(5):
        mind.world.update("a sudden violent attack", ["threat", "alarm"])
        mind.world.update("a burst of warm praise", ["reward", "praise"])
    ranked = mind.foresee(
        [
            ("danger", _stim("a sudden violent attack", tags=["threat", "alarm"])),
            ("warmth", _stim("a burst of warm praise", tags=["reward", "praise"])),
        ]
    )
    assert ranked[0].option == "warmth"  # she'd rather the pleasant future
    assert ranked[0].affect.valence > ranked[-1].affect.valence


def test_the_novel_future_is_more_appealing_than_the_stale_one() -> None:
    mind = Mind(settings=Settings())
    # Make one topic thoroughly familiar so it carries no novelty.
    for _ in range(6):
        mind.perceive(_stim("the plain grey wall is here", tags=["place"]))
    ranked = mind.foresee(
        [
            ("the wall again", _stim("the plain grey wall is here", tags=["place"])),
            ("somewhere new", _stim("an unfamiliar shimmering doorway", tags=["place"])),
        ]
    )
    assert ranked[0].option == "somewhere new"
    assert ranked[0].novelty > ranked[-1].novelty


def test_live_uses_foresight_to_explore_the_whole_house() -> None:
    from sentiance.live import run_live
    from sentiance.world import World, default_home

    mind = Mind(settings=Settings())  # simulated backend — offline
    world = World(places=default_home().places, current="bedroom")
    run_live(mind, world, steps=30)
    # Over a while, foresight (plus restlessness) carries her beyond the first
    # room — she reaches more than one place, not stuck where she woke.
    assert len(world.visited) >= 3
