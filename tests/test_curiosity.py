"""Intrinsic curiosity — the epistemic drive toward, and reward from, the unknown."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind
from sentiance.mind.curiosity import Curiosity, wonder_key
from sentiance.mind.state import Drive, Stimulus


def _stim(content: str, **kw: object) -> Stimulus:
    return Stimulus(content=content, intensity=0.6, **kw)  # type: ignore[arg-type]


def test_hunger_rises_as_the_curiosity_drive_falls() -> None:
    c = Curiosity()
    assert c.hunger({Drive.CURIOSITY: 0.9}) < c.hunger({Drive.CURIOSITY: 0.1})


def test_the_bonus_favours_the_informative_more_when_hungry() -> None:
    c = Curiosity()
    hungry = c.appeal_bonus({Drive.CURIOSITY: 0.1})
    sated = c.appeal_bonus({Drive.CURIOSITY: 0.9})
    novel_stim = _stim("something entirely new")
    # A novel option earns a bigger pull when she's epistemically hungry.
    assert hungry(novel_stim, 0.9) > sated(novel_stim, 0.9)
    # And novelty matters: the unknown pulls harder than the familiar.
    assert hungry(novel_stim, 0.9) > hungry(novel_stim, 0.1)


def test_understanding_something_once_surprising_is_rewarded() -> None:
    c = Curiosity()
    # First encounter: surprising, so she starts wondering about it (no reward yet).
    assert c.observe("a strange humming machine", novelty=0.9) == 0.0
    # Later, the same thing is familiar — it clicks, and understanding feels good.
    reward = c.observe("a strange humming machine", novelty=0.1)
    assert reward > 0.0
    # The wonder is spent — it doesn't pay out twice.
    assert c.observe("a strange humming machine", novelty=0.1) == 0.0


def test_wonder_key_names_what_a_moment_is_about() -> None:
    assert wonder_key("I am in the kitchen") == "kitchen"
    assert wonder_key("the old clock") == "clock"


def test_curiosity_drives_a_mind_to_explore_its_whole_world() -> None:
    from sentiance.live import run_live
    from sentiance.world import World, default_home

    mind = Mind(settings=Settings())  # simulated backend — offline
    world = World(places=default_home().places, current="bedroom")
    run_live(mind, world, steps=45)
    # Drawn to the unfamiliar, she doesn't circle known rooms — she finds them all.
    assert set(world.visited) == {"bedroom", "hallway", "kitchen", "garden"}


def test_an_aha_lifts_feeling_and_persists(tmp_path) -> None:
    mind = Mind(settings=Settings())
    # Meet something novel, then meet it again once it's familiar → an "aha".
    for _ in range(4):
        mind.perceive(_stim("a peculiar glowing orb", tags=["object"]))
    # By now the orb is familiar; a fresh encounter should register understanding.
    mind.curiosity._wondered["orb"] = 0.9  # she had wondered about it
    before = mind.affect.valence
    mind.perceive(_stim("a peculiar glowing orb", tags=["object"]))
    assert mind.affect.valence >= before  # understanding didn't sour her mood
    # Curiosity's wonder-state survives a save/restore.
    path = tmp_path / "aria.json"
    mind.curiosity._wondered["mystery"] = 0.8
    mind.save(str(path))
    reborn = Mind(settings=Settings())
    reborn.load(str(path))
    assert "mystery" in reborn.curiosity._wondered
