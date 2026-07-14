"""Frustration & anger — a thwarted intention that turns to approach, not retreat."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind
from sentiance.mind.frustration import Frustration
from sentiance.mind.state import Emotion, Stimulus


def test_being_blocked_builds_frustration_until_it_boils_over() -> None:
    f = Frustration()
    assert not f.angry
    for _ in range(4):
        f.update(has_goal=True, goal_congruence=-0.4)
    assert f.angry  # repeated thwarting crosses the threshold


def test_an_unblocked_life_never_gets_angry() -> None:
    f = Frustration()
    for _ in range(10):
        f.update(has_goal=True, goal_congruence=0.5)  # things are going her way
    assert not f.angry
    assert f.level == 0.0


def test_relief_vents_the_pressure() -> None:
    f = Frustration()
    for _ in range(4):
        f.update(has_goal=True, goal_congruence=-0.4)
    high = f.level
    f.relieve()
    assert f.level < high


def test_frustration_only_builds_when_she_actually_wants_something() -> None:
    f = Frustration()
    for _ in range(10):
        f.update(has_goal=False, goal_congruence=-0.8)  # bad, but nothing at stake
    assert f.level == 0.0


def test_a_persistently_blocked_goal_turns_to_anger_and_persistence() -> None:
    mind = Mind(settings=Settings())
    mind.perceive(Stimulus(content="I want to open the locked door", intensity=0.7))
    assert mind.state().goals  # she has taken on the intention

    saw_anger = False
    for _ in range(6):
        mind.perceive(
            Stimulus(content="the locked door will not budge", intensity=0.7, tags=["loss"])
        )
        if mind.affect.emotion is Emotion.ANGER:
            saw_anger = True

    assert mind.frustration.angry  # the block wore on her
    assert saw_anger  # and it showed as anger, not just fear
    # Anger fuels the pursuit: the thwarted goal stays urgent instead of fading away.
    top = mind.goals.top()
    assert top is not None and top.urgency > 0.6
