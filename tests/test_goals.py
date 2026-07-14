"""Goals & intentions — forming, holding, pursuing, resolving."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind, Stimulus
from sentiance.mind.goals import GoalSystem
from sentiance.mind.state import (
    AffectState,
    Appraisal,
    ConsciousMoment,
    ContentSource,
    Drive,
    Emotion,
    GoalStatus,
)


def _moment(content: str, emotion: Emotion, tick: int = 1) -> ConsciousMoment:
    return ConsciousMoment(
        tick=tick,
        content=content,
        source=ContentSource.THOUGHT,
        salience=0.6,
        affect=AffectState(emotion=emotion),
        attention_target=content,
    )


def _appraisal() -> Appraisal:
    return Appraisal(novelty=0.7, goal_congruence=0.0, control=0.6, relevance=0.6)


def test_explicit_intention_becomes_a_goal() -> None:
    gs = GoalSystem()
    events = gs.update(
        _moment("I should check where that sound came from", Emotion.CURIOSITY),
        _appraisal(),
        Drive.CURIOSITY,
        AffectState(emotion=Emotion.CURIOSITY),
        {Drive.SAFETY: 0.9},
    )
    assert ("formed", gs.active()[0]) in events
    assert "check where that sound came from" in gs.descriptions()[0]


def test_threat_forms_a_safety_goal_that_resolves_when_safe() -> None:
    gs = GoalSystem()
    gs.update(
        _moment("a sudden crash", Emotion.FEAR),
        _appraisal(),
        Drive.SAFETY,
        AffectState(emotion=Emotion.FEAR),
        {Drive.SAFETY: 0.2},  # unsafe
    )
    goal = gs.active()[0]
    assert goal.drive is Drive.SAFETY

    # Once safety recovers, the goal resolves.
    gs.update(
        _moment("the room is quiet again", Emotion.CONTENTMENT, tick=2),
        _appraisal(),
        Drive.SAFETY,
        AffectState(emotion=Emotion.CONTENTMENT),
        {Drive.SAFETY: 0.9},  # safe again
    )
    assert goal.status is GoalStatus.RESOLVED
    assert not gs.active()


def test_goal_is_abandoned_when_it_goes_stale() -> None:
    gs = GoalSystem()
    gs.update(
        _moment("I should find the blue key", Emotion.CURIOSITY),
        _appraisal(),
        Drive.CURIOSITY,
        AffectState(emotion=Emotion.CURIOSITY),
        {Drive.SAFETY: 0.9},
    )
    # Many unrelated ticks — urgency decays with nothing feeding it.
    for t in range(2, 12):
        gs.update(
            _moment("clouds drift by", Emotion.NEUTRAL, tick=t),
            _appraisal(),
            Drive.COHERENCE,
            AffectState(),
            {Drive.SAFETY: 0.9},
        )
    assert not gs.active()  # let go of


def test_goal_shows_in_mind_state_and_persists(tmp_path) -> None:
    mind = Mind(settings=Settings())
    mind.perceive(Stimulus(content="I should check the noise", intensity=0.6, tags=["reflection"]))
    assert mind.state().goals  # an intention is now held

    path = tmp_path / "aria.json"
    mind.save(str(path))
    reborn = Mind(settings=Settings())
    reborn.load(str(path))
    assert reborn.goals.active()  # the intention survived the round trip
