"""Empathy — catching another's feeling, more from those she's close to."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind
from sentiance.mind.empathy import Empathy
from sentiance.mind.state import Stimulus


def _befriend(mind: Mind, name: str, times: int = 15) -> None:
    for _ in range(times):
        mind.perceive(Stimulus(content=f"@{name} holds my hand warmly", intensity=0.7,
                               tags=["friend", "warmth", "reward"]))


def test_reads_joy_and_sorrow_from_how_a_person_is_described() -> None:
    e = Empathy()
    joy = e.read("@Sam is laughing, delighted")
    sorrow = e.read("@Sam is sobbing, heartbroken")
    assert joy is not None and joy[0] > 0
    assert sorrow is not None and sorrow[0] < 0
    # No emotional cue → nothing to catch.
    assert e.read("@Sam walks across the room") is None


def test_closeness_deepens_the_contagion() -> None:
    e = Empathy()
    assert e.contagion(0.9) > e.contagion(0.0)
    assert 0.0 <= e.contagion(0.0) <= 1.0


def test_a_friends_sorrow_moves_her_more_than_a_strangers() -> None:
    close = Mind(settings=Settings())
    _befriend(close, "Sam")
    v_close = close.perceive(Stimulus(content="@Sam is sobbing and heartbroken",
                                      intensity=0.6)).moment.affect.valence

    stranger = Mind(settings=Settings())
    v_stranger = stranger.perceive(Stimulus(content="@Sam is sobbing and heartbroken",
                                            intensity=0.6)).moment.affect.valence

    assert close.last_empathy is not None and close.last_empathy[0] == "Sam"
    assert v_close < v_stranger  # the friend's grief pulls her down further


def test_a_loved_ones_joy_leaves_her_brighter_than_their_sorrow() -> None:
    happy = Mind(settings=Settings())
    _befriend(happy, "Sam")
    happy.perceive(Stimulus(content="@Sam is laughing with delight", intensity=0.6))

    blue = Mind(settings=Settings())
    _befriend(blue, "Sam")
    blue.perceive(Stimulus(content="@Sam is weeping with grief", intensity=0.6))

    assert happy.last_empathy is not None and blue.last_empathy is not None
    assert happy.affect.valence > blue.affect.valence  # their mood carries into hers


def test_no_person_present_means_no_contagion() -> None:
    mind = Mind(settings=Settings())
    mind.perceive(Stimulus(content="the wind is sobbing through the trees", intensity=0.5))
    assert mind.last_empathy is None  # a turn of phrase, not a person's feeling
