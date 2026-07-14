"""Attachment / love — bonds that deepen, warm her near, and are missed when gone."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind
from sentiance.mind.relationships import RelationshipSystem
from sentiance.mind.state import Stimulus


def test_warmth_over_time_deepens_the_bond() -> None:
    r = RelationshipSystem()
    for t in range(12):
        r.record(["Mara"], valence=0.8, tick=t)
    assert r.known("Mara").attachment > 0.5  # many warm encounters → a real bond
    # A single meeting barely bonds at all.
    r.record(["Stranger"], valence=0.8, tick=99)
    assert r.known("Stranger").attachment < 0.1


def test_the_bond_is_the_strongest_attachment_present() -> None:
    r = RelationshipSystem()
    for t in range(12):
        r.record(["Mara"], valence=0.8, tick=t)
    assert r.bond(["Mara"]) > 0.5
    assert r.bond(["Nobody"]) == 0.0  # strangers carry no bond


def test_a_loved_one_is_missed_more_the_longer_theyre_gone() -> None:
    r = RelationshipSystem()
    for t in range(12):
        r.record(["Mara"], valence=0.9, tick=t)
    near = r.missing(current_tick=20, present=set())  # gone a little while
    far = r.missing(current_tick=60, present=set())  # gone much longer
    assert near is not None and far is not None
    assert far[1] > near[1]  # longing grows with time apart
    # ...but not while they're right here.
    assert r.missing(current_tick=60, present={"Mara"}) is None
    # A barely-known person isn't missed at all.
    r.record(["Acq"], valence=0.2, tick=0)
    got = r.missing(current_tick=60, present=set())
    assert got is None or got[0] == "Mara"


def test_a_present_loved_one_lifts_her_and_absence_leaves_her_lonelier() -> None:
    mind = Mind(settings=Settings())
    for _ in range(15):
        mind.perceive(Stimulus(content="@Mara holds my hand warmly", intensity=0.7,
                               tags=["friend", "warmth", "reward"]))
    assert mind.relationships.known("Mara").attachment > 0.4

    # She goes a long time without Mara — and comes to miss her.
    for _ in range(30):
        mind.idle()
    assert mind.longing is not None
    assert mind.longing[0] == "Mara"
    assert mind.needs.connection < 0.35  # the absence has left her lonely


def test_attachment_persists_across_a_reload(tmp_path) -> None:
    mind = Mind(settings=Settings())
    for _ in range(12):
        mind.perceive(Stimulus(content="@Mara smiles at me", intensity=0.7,
                               tags=["friend", "warmth"]))
    path = tmp_path / "aria.json"
    mind.save(str(path))
    reborn = Mind(settings=Settings())
    reborn.load(str(path))
    assert abs(reborn.relationships.known("Mara").attachment
               - mind.relationships.known("Mara").attachment) < 1e-6
