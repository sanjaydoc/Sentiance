"""Relationships & theory-of-mind — knowing people across encounters."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind, Stimulus
from sentiance.mind.relationships import RelationshipSystem, extract_people


def test_extract_people() -> None:
    assert extract_people("@Sam and @Mara wave, and @Sam smiles again") == ["Sam", "Mara"]
    assert extract_people("just the wind") == []


def test_warm_encounters_build_affection_and_trust() -> None:
    rs = RelationshipSystem()
    for t in range(1, 5):
        rs.record(["Sam"], valence=0.6, tick=t)
    sam = rs.known("Sam")
    assert sam.encounters == 4
    assert sam.affection > 0.3
    assert sam.trust > 0.5
    assert rs.prior(["Sam"]) == sam.affection


def test_hurtful_encounters_sour_the_bond() -> None:
    rs = RelationshipSystem()
    for t in range(1, 5):
        rs.record(["Rex"], valence=-0.7, tick=t)
    rex = rs.known("Rex")
    assert rex.affection < -0.3
    assert rex.trust < 0.5


def test_known_friend_colors_appraisal_on_sight() -> None:
    mind = Mind(settings=Settings())
    # Build a warm history with Sam.
    for _ in range(4):
        mind.perceive(Stimulus(content="@Sam greets me warmly", intensity=0.6, tags=["friend"]))
    assert mind.relationships.known("Sam").affection > 0.2

    # A neutral line that merely mentions Sam now lands positive (the bond colors it).
    friend = mind.perceive(Stimulus(content="@Sam is here", intensity=0.4))
    stranger = mind.perceive(Stimulus(content="@Nobody is here", intensity=0.4))
    assert friend.moment.affect.valence > stranger.moment.affect.valence


def test_relationships_persist(tmp_path) -> None:
    mind = Mind(settings=Settings())
    mind.perceive(Stimulus(content="@Sam laughs with me", intensity=0.6, tags=["friend"]))
    path = tmp_path / "aria.json"
    mind.save(str(path))

    reborn = Mind(settings=Settings())
    reborn.load(str(path))
    assert reborn.relationships.known("Sam") is not None
