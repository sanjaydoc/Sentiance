"""Felt time & anticipation — hope and dread about what is coming."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind
from sentiance.mind.anticipation import Anticipation, points_forward
from sentiance.mind.state import Emotion, Stimulus


def test_recognizes_when_a_moment_points_forward() -> None:
    assert points_forward("a storm will come at nightfall")
    assert points_forward("@Sam is going to visit tomorrow")
    assert not points_forward("the room is quiet and still")


def test_a_charged_future_becomes_an_expectation() -> None:
    a = Anticipation()
    assert a.note("a storm is coming soon", ["storm", "threat"], now=0) is not None
    assert a.note("the wall is grey", ["place"], now=1) is None  # nothing foretold
    assert a.note("later it will simply be", [], now=2) is None  # foretold, but no charge
    assert len(a.pending) == 1


def test_anticipation_swells_as_the_hour_approaches() -> None:
    a = Anticipation()
    a.note("a dreadful reckoning is coming", ["threat"], now=0)  # due at 8
    early = a.feeling(now=1)
    late = a.feeling(now=7)
    assert early is not None and late is not None
    assert abs(late[0]) > abs(early[0])  # dread presses harder the nearer it is
    assert late[2] is Emotion.DREAD


def test_hope_and_dread_pull_opposite_ways() -> None:
    good = Anticipation()
    good.note("a joyful reunion is coming", ["reward", "friend"], now=0)
    bad = Anticipation()
    bad.note("a painful trial is coming", ["threat"], now=0)
    gv, _, gemo = good.feeling(now=6)
    bv, _, bemo = bad.feeling(now=6)
    assert gv > 0 and gemo is Emotion.HOPE
    assert bv < 0 and bemo is Emotion.DREAD


def test_the_awaited_arrives_and_clears() -> None:
    a = Anticipation()
    a.note("a storm is coming", ["storm", "threat"], now=0)
    assert a.due(now=4) == []  # not yet
    arrived = a.due(now=8)
    assert len(arrived) == 1
    assert a.pending == []  # once it's here, it's no longer awaited


def test_a_looming_dread_weighs_on_her_then_passes() -> None:
    mind = Mind(settings=Settings())
    mind.perceive(Stimulus(content="a terrible storm will come by nightfall",
                           intensity=0.6, tags=["storm", "threat"]))
    saw_dread = False
    valences = []
    for _ in range(8):
        r = mind.idle()
        valences.append(r.moment.affect.valence)
        if r.moment.affect.emotion is Emotion.DREAD:
            saw_dread = True
    assert saw_dread  # the looming storm comes to weigh on her
    assert valences[-1] < valences[0]  # her mood sinks as it nears


def test_a_good_thing_coming_lifts_her() -> None:
    mind = Mind(settings=Settings())
    base = mind.idle().moment.affect.valence
    mind.perceive(Stimulus(content="a warm reunion with friends is coming tomorrow",
                           intensity=0.5, tags=["reward", "friend", "warmth"]))
    lift = mind.idle().moment.affect.valence
    assert lift > base  # hope brightens the present
    assert mind.last_anticipation is not None


def test_expectations_persist_across_a_reload(tmp_path) -> None:
    mind = Mind(settings=Settings())
    mind.perceive(Stimulus(content="a storm is coming soon", intensity=0.6,
                           tags=["storm", "threat"]))
    assert mind.anticipation.pending
    path = tmp_path / "aria.json"
    mind.save(str(path))
    reborn = Mind(settings=Settings())
    reborn.load(str(path))
    assert len(reborn.anticipation.pending) == len(mind.anticipation.pending)
