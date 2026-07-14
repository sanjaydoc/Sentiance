"""Volition & self-control — holding focus by effort, until the reserve runs dry."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind
from sentiance.mind.state import Candidate, ContentSource, Stimulus
from sentiance.mind.volition import Volition


def _scene() -> list[Candidate]:
    return [
        Candidate(content="a dazzling distraction", source=ContentSource.PERCEPT, salience=0.8),
        Candidate(content="my intention to finish the work", source=ContentSource.THOUGHT,
                  salience=0.4),
    ]


def _leader(cands: list[Candidate]) -> int:
    return max(range(len(cands)), key=lambda i: cands[i].salience)


def test_with_willpower_she_overrides_a_distraction() -> None:
    v = Volition()
    cands = _scene()
    assert _leader(cands) == 0  # the distraction is louder on its own
    exerted = v.focus(cands, [False, True])
    assert exerted
    assert _leader(cands) == 1  # she pulls focus back to the goal
    assert v.effort < 1.0  # at a cost


def test_when_the_reserve_is_spent_the_impulse_wins() -> None:
    v = Volition()
    held = succumbed = 0
    for _ in range(12):
        cands = _scene()
        v.focus(cands, [False, True])
        if _leader(cands) == 1:
            held += 1
        else:
            succumbed += 1
    assert held >= 1  # she resists for a while
    assert succumbed >= 1  # ...then willpower runs out and she gives in


def test_no_effort_spent_when_already_focused() -> None:
    v = Volition()
    # The goal-relevant candidate is already the most salient.
    cands = [
        Candidate(content="the distraction", source=ContentSource.PERCEPT, salience=0.3),
        Candidate(content="my goal", source=ContentSource.THOUGHT, salience=0.7),
    ]
    exerted = v.focus(cands, [False, True])
    assert not exerted
    assert v.effort == 1.0  # no willpower needed when the goal already holds


def test_rest_restores_willpower() -> None:
    v = Volition()
    for _ in range(20):
        v.focus(_scene(), [False, True])
    assert v.effort < 0.5
    v.restore()
    assert v.effort == 1.0


def test_she_resists_a_feeling_to_stay_with_her_intention() -> None:
    mind = Mind(settings=Settings())
    mind.perceive(Stimulus(content="I want to finish writing the letter", intensity=0.6))
    assert mind.state().goals
    # A jolt spikes her arousal, leaving a strong feeling that lingers.
    mind.perceive(Stimulus(content="a sudden alarming jolt", intensity=0.9,
                           tags=["threat", "alarm"]))

    exerted = False
    held_the_goal = False
    for _ in range(6):  # bland moments where the leftover feeling would take over
        result = mind.perceive(Stimulus(content="the plain wall", intensity=0.15))
        if mind.last_effort:
            exerted = True
            # When she exerts, her intention wins the spotlight, not the raw feeling.
            if not result.moment.content.startswith("a feeling of"):
                held_the_goal = True
    assert exerted  # she spent effort to resist the impulse
    assert held_the_goal


def test_sleep_renews_willpower_in_the_mind() -> None:
    mind = Mind(settings=Settings())
    mind.volition.effort = 0.2  # worn down
    mind.sleep()
    assert mind.volition.effort == 1.0  # a night's rest restores self-control
