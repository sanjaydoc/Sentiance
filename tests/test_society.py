"""A society — minds sharing one house, meeting and bonding through the world."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind
from sentiance.society import Inhabitant, Society
from sentiance.world import World, default_home


def _pair(room_a: str, room_b: str) -> tuple[Inhabitant, Inhabitant]:
    places = default_home().places  # shared rooms, separate bodies
    ada = Inhabitant("Ada", Mind(settings=Settings(agent_name="Ada")),
                     World(places=places, current=room_a))
    bo = Inhabitant("Bo", Mind(settings=Settings(agent_name="Bo")),
                    World(places=places, current=room_b))
    return ada, bo


def test_two_minds_in_a_room_come_to_know_and_bond_with_each_other() -> None:
    ada, bo = _pair("kitchen", "kitchen")
    society = Society([ada, bo])
    for _ in range(12):
        society.step()
    assert ada.mind.relationships.known("Bo") is not None
    assert bo.mind.relationships.known("Ada") is not None
    assert ada.mind.relationships.known("Bo").attachment > 0.3  # repeated warmth bonds them
    assert bo.mind.relationships.known("Ada").attachment > 0.3


def test_a_mind_never_befriends_itself() -> None:
    ada, bo = _pair("kitchen", "kitchen")
    society = Society([ada, bo])
    for _ in range(10):
        society.step()
    # Even though names get voiced in speech, she forms no relationship with herself.
    assert ada.mind.relationships.known("Ada") is None
    assert bo.mind.relationships.known("Bo") is None


def test_housemates_catch_each_others_feelings() -> None:
    ada, bo = _pair("kitchen", "kitchen")
    society = Society([ada, bo])
    caught = False
    for _ in range(12):
        for _who, _affect, _perceived, notes in society.step():
            if any("catches" in n for n in notes):
                caught = True
    assert caught  # what one feels carries to the other through their words


def test_a_lonely_mind_goes_looking_for_company() -> None:
    # Start them apart (bedroom and garden are both a couple of rooms away).
    ada, bo = _pair("bedroom", "garden")
    society = Society([ada, bo])
    met = False
    for _ in range(20):
        society.step()
        if ada.room == bo.room:
            met = True
            break
    assert met  # loneliness drew them into the same room


def test_a_trio_breaks_up_so_every_pair_gets_to_meet() -> None:
    from sentiance.society import _cast

    society = Society(_cast())
    for _ in range(40):
        society.step()
    # Because a crowd sheds a wanderer, no one is stuck only knowing the popular
    # housemate — each of the three comes to know *both* of the others.
    for me in society.inhabitants:
        known = set(me.mind.relationships.people)
        others = {other.name for other in society.inhabitants if other.name != me.name}
        assert known == others


def test_the_bond_they_build_persists_across_a_reload(tmp_path) -> None:
    ada, bo = _pair("kitchen", "kitchen")
    society = Society([ada, bo])
    for _ in range(12):
        society.step()
    path = tmp_path / "ada.json"
    ada.mind.save(str(path))
    reborn = Mind(settings=Settings(agent_name="Ada"))
    reborn.load(str(path))
    assert reborn.relationships.known("Bo") is not None  # she remembers her housemate
