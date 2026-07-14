"""Self-conscious emotions — pride and disappointment, measured against her
own standards."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind
from sentiance.mind.conscience import Conscience
from sentiance.mind.state import Emotion, Goal, Stimulus


def _goal(desc: str, urgency: float = 0.6) -> Goal:
    from sentiance.mind.state import Drive

    return Goal(
        description=desc, drive=Drive.CURIOSITY, created_tick=1, updated_tick=1, urgency=urgency
    )


def test_following_through_breeds_pride() -> None:
    j = Conscience().judge([("resolved", _goal("understand the sound"))])
    assert j is not None
    assert j.emotion is Emotion.PRIDE
    assert j.valence > 0


def test_letting_go_breeds_disappointment() -> None:
    j = Conscience().judge([("abandoned", _goal("tidy the room"))])
    assert j is not None
    assert j.emotion is Emotion.DISAPPOINTMENT
    assert j.valence < 0


def test_pride_scales_with_how_much_the_goal_mattered() -> None:
    strong = Conscience().judge([("resolved", _goal("x", urgency=0.9))])
    weak = Conscience().judge([("resolved", _goal("y", urgency=0.1))])
    assert strong is not None and weak is not None
    assert strong.valence > weak.valence


def test_nothing_resolved_or_abandoned_is_no_self_judgment() -> None:
    assert Conscience().judge([("formed", _goal("start something"))]) is None
    assert Conscience().judge([]) is None


def test_resolving_a_pursued_intention_makes_her_proud() -> None:
    mind = Mind(settings=Settings())
    mind.perceive(Stimulus(content="I want to explore the garden", intensity=0.6))
    assert mind.state().goals  # she took it on
    # Pursue it until it's done.
    mind.perceive(Stimulus(content="explore the garden path", intensity=0.6))
    mind.perceive(Stimulus(content="explore the garden path again", intensity=0.6))

    assert not mind.state().goals  # the intention is fulfilled
    assert mind.last_self_judgment is not None
    assert mind.last_self_judgment.emotion is Emotion.PRIDE
    # The pride colours the feeling she now carries and how she sees herself.
    assert mind.affect.emotion is Emotion.PRIDE
    assert mind.affect.valence > 0
    assert mind.state().affect.emotion is Emotion.PRIDE
