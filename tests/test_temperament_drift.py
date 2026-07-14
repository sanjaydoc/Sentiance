"""Temperament drift — lived experience slowly reshaping who she is."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind, Stimulus
from sentiance.mind.temperament import Temperament


def test_a_life_that_keeps_turning_out_well_makes_her_more_optimistic() -> None:
    t = Temperament(optimism=0.5, plasticity=0.1)
    for _ in range(30):
        t.drift(novelty=0.2, valence=0.7, arousal=0.4, control=0.8)
    assert t.optimism > 0.6
    # ...and a bleak life dims it.
    d = Temperament(optimism=0.5, plasticity=0.1)
    for _ in range(30):
        d.drift(novelty=0.2, valence=-0.7, arousal=0.4, control=0.5)
    assert d.optimism < 0.4


def test_repeated_helpless_fright_makes_her_warier() -> None:
    anx = Temperament(anxiety=0.5, plasticity=0.1)
    for _ in range(30):
        anx.drift(novelty=0.5, valence=-0.8, arousal=0.8, control=0.1)  # bad + no control
    assert anx.anxiety > 0.6
    # Safety she can control calms her over time.
    calm = Temperament(anxiety=0.5, plasticity=0.1)
    for _ in range(30):
        calm.drift(novelty=0.2, valence=0.6, arousal=0.3, control=0.9)
    assert calm.anxiety < 0.4


def test_curiosity_shifts_only_with_novelty_and_by_how_it_pays_off() -> None:
    rewarded = Temperament(curiosity=0.5, plasticity=0.1)
    punished = Temperament(curiosity=0.5, plasticity=0.1)
    ignored = Temperament(curiosity=0.5, plasticity=0.1)
    for _ in range(30):
        rewarded.drift(novelty=0.9, valence=0.8, arousal=0.6, control=0.7)
        punished.drift(novelty=0.9, valence=-0.8, arousal=0.6, control=0.3)
        ignored.drift(novelty=0.1, valence=0.8, arousal=0.6, control=0.7)  # nothing new
    assert rewarded.curiosity > 0.65  # the new keeps rewarding her → bolder
    assert punished.curiosity < 0.35  # the new keeps hurting → warier of it
    assert abs(ignored.curiosity - 0.5) < 0.02  # no novelty → curiosity doesn't learn


def test_drift_is_bounded_and_slow_by_default() -> None:
    t = Temperament(optimism=0.5)  # default plasticity ~0.01
    for _ in range(20):
        t.drift(novelty=0.5, valence=1.0, arousal=0.5, control=0.5)
    assert 0.5 < t.optimism < 0.62  # moved, but only a little — character is stable
    assert 0.0 <= t.optimism <= 1.0


def test_who_she_becomes_survives_and_reports_the_change() -> None:
    warm = Mind(settings=Settings())  # innate 0.5 across the board
    for _ in range(50):
        warm.perceive(Stimulus(content="a warm friend praises me", intensity=0.7,
                               tags=["reward", "praise", "warmth", "friend"]))
    # A kind life has bent her disposition away from where she began.
    assert warm.temperament.optimism > 0.55
    assert warm.temperament.anxiety < 0.45
    assert warm.temperament.drift_from_innate()["optimism"] > 0

    # And that changed self persists across a save/reload — including her innate baseline.
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as d:
        path = str(Path(d) / "aria.json")
        warm.save(path)
        reborn = Mind(settings=Settings(temperament_optimism=0.5))
        reborn.load(path)
        assert abs(reborn.temperament.optimism - warm.temperament.optimism) < 1e-6
        assert reborn.temperament.innate == warm.temperament.innate
