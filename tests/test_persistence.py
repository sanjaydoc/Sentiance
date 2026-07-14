"""Durable identity — a mind's memory and inner state survive across runs."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind, Stimulus
from sentiance.mind.persistence import load, save


def _lived_mind() -> Mind:
    mind = Mind(settings=Settings())
    mind.perceive(Stimulus(content="a friend calls my name", intensity=0.6, tags=["friend"]))
    mind.perceive(Stimulus(content="a sudden crash", intensity=0.9, tags=["threat"]))
    for _ in range(3):
        mind.idle()
    return mind


def test_round_trip_restores_identity(tmp_path) -> None:
    original = _lived_mind()
    path = tmp_path / "aria.json"
    save(original, path)

    reborn = Mind(settings=Settings())
    recovered = load(reborn, path)

    assert recovered == len(original.memory.episodic) > 0
    assert reborn.tick_no == original.tick_no
    assert reborn.self_model.narrative == original.self_model.narrative
    assert reborn.drives.levels == original.drives.levels
    # A previously-seen word is now familiar to the reborn mind (world-model kept).
    assert reborn.world.surprise("friend calls", ["friend"]) < 0.9


def test_reborn_mind_continues_the_stream(tmp_path) -> None:
    original = _lived_mind()
    path = tmp_path / "aria.json"
    save(original, path)

    reborn = Mind(settings=Settings())
    load(reborn, path)
    next_tick = reborn.tick_no + 1
    result = reborn.idle()
    assert result.moment.tick == next_tick  # picks up where it left off


def test_load_missing_file_returns_zero(tmp_path) -> None:
    mind = Mind(settings=Settings())
    assert load(mind, tmp_path / "nope.json") == 0


def test_mind_save_load_methods(tmp_path) -> None:
    original = _lived_mind()
    path = str(tmp_path / "aria.json")
    original.save(path)
    reborn = Mind(settings=Settings())
    assert reborn.load(path) > 0
