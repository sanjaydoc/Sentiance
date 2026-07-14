"""Temperament & needs — individuality and intrinsic wants."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind, Stimulus
from sentiance.mind.state import Appraisal
from sentiance.mind.temperament import Needs, Temperament


def test_anxious_vs_optimistic_shape_the_same_threat_differently() -> None:
    bad = Appraisal(novelty=0.5, goal_congruence=-0.5, control=0.5, relevance=0.6)
    anxious = Temperament(anxiety=0.9, optimism=0.2).shape(bad)
    optimistic = Temperament(anxiety=0.2, optimism=0.9).shape(bad)
    assert anxious.goal_congruence < bad.goal_congruence  # anxiety deepens the bad
    assert anxious.control < bad.control  # ...and lowers felt control
    assert optimistic.goal_congruence > anxious.goal_congruence  # optimism lifts it


def test_curiosity_rewards_novelty() -> None:
    novel = Appraisal(novelty=0.9, goal_congruence=0.0, control=0.6, relevance=0.5)
    curious = Temperament(curiosity=0.9).shape(novel)
    incurious = Temperament(curiosity=0.1).shape(novel)
    assert curious.goal_congruence > incurious.goal_congruence


def test_needs_deplete_and_create_pressure() -> None:
    needs = Needs(rest=0.7, stimulation=0.6, connection=0.6)
    assert needs.pressure() == 0.0  # satisfied → no pressure
    # Many dull, unsocial moments: stimulation and connection fall.
    for _ in range(10):
        needs.step(novelty=0.0, arousal=0.2, social=False, valence=0.0)
    assert needs.stimulation < 0.35  # bored
    assert needs.connection < 0.35  # lonely
    assert needs.pressure() < 0.0  # unmet needs now weigh on her
    assert needs.most_pressing() in {"stimulation", "connection", "rest"}


def test_warm_company_replenishes_connection() -> None:
    needs = Needs(connection=0.3)
    needs.step(novelty=0.3, arousal=0.4, social=True, valence=0.6)
    assert needs.connection > 0.3


def test_an_anxious_mind_feels_a_threat_more_than_an_optimistic_one() -> None:
    anxious = Mind(settings=Settings(temperament_anxiety=0.95, temperament_optimism=0.1))
    sunny = Mind(settings=Settings(temperament_anxiety=0.1, temperament_optimism=0.95))
    stim = Stimulus(content="a sudden loud crash", intensity=0.9, tags=["threat", "alarm"])
    assert anxious.perceive(stim).moment.affect.valence < sunny.perceive(stim).moment.affect.valence


def test_needs_persist(tmp_path) -> None:
    mind = Mind(settings=Settings())
    for _ in range(6):
        mind.idle()  # deplete stimulation a bit
    path = tmp_path / "aria.json"
    mind.save(str(path))
    reborn = Mind(settings=Settings())
    reborn.load(str(path))
    assert abs(reborn.needs.stimulation - mind.needs.stimulation) < 1e-6
