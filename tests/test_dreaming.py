"""Dreaming — recombining memory into something new, and waking changed."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind
from sentiance.mind.dreaming import dream
from sentiance.mind.state import Stimulus


def _remember(mind: Mind, content: str, tags: list[str], times: int = 3) -> None:
    for _ in range(times):
        mind.perceive(Stimulus(content=content, intensity=0.8, tags=tags))


def test_no_dream_without_enough_charged_memory() -> None:
    mind = Mind(settings=Settings())
    assert dream(mind.memory, tick=1) is None  # nothing to dream on yet


def test_a_dream_weaves_several_memories_together() -> None:
    mind = Mind(settings=Settings())
    _remember(mind, "a bright kite over the meadow", ["reward", "beauty"])
    _remember(mind, "a cold wave on jagged rocks", ["threat"])
    d = dream(mind.memory, tick=3)
    assert d is not None
    assert "I dreamt of" in d.narrative
    assert len(d.fragments) >= 2


def test_dreaming_is_deterministic_in_the_tick() -> None:
    mind = Mind(settings=Settings())
    _remember(mind, "a bright kite over the meadow", ["reward", "beauty"])
    _remember(mind, "a cold wave on jagged rocks", ["threat"])
    _remember(mind, "a warm lamp in the window", ["warmth", "reward"])
    assert dream(mind.memory, tick=5).narrative == dream(mind.memory, tick=5).narrative


def test_sleeping_forges_associations_she_never_made_awake() -> None:
    mind = Mind(settings=Settings())
    _remember(mind, "a bright kite over the meadow", ["reward", "beauty"])
    _remember(mind, "a cold wave on jagged rocks", ["threat"])
    # 'kite' and 'rocks' never co-occurred while awake.
    assert mind.memory.semantic.get("kite", {}).get("rocks", 0) == 0

    mind.sleep()
    # The dream stitched them together — a new link between distant ideas.
    assert mind.memory.semantic.get("kite", {}).get("rocks", 0) > 0
    assert mind.last_dream is not None
    # She wakes remembering the dream itself.
    assert any("dream" in t.tags for t in mind.memory.episodic)


def test_a_vivid_dream_leaves_a_new_intention() -> None:
    mind = Mind(settings=Settings())
    # Strongly-charged memories → a dream hot enough to want explaining.
    _remember(mind, "a joyful reunion full of warmth", ["reward", "warmth", "praise"], times=5)
    _remember(mind, "a triumphant summit under open sky", ["reward", "beauty"], times=5)
    before = len(mind.state().goals)
    mind.sleep()
    assert mind.last_dream is not None and abs(mind.last_dream.tone) >= 0.4
    assert any("dream" in g for g in mind.state().goals)
    assert len(mind.state().goals) > before


def test_the_dream_survives_a_reload(tmp_path) -> None:
    mind = Mind(settings=Settings())
    _remember(mind, "a bright kite over the meadow", ["reward", "beauty"])
    _remember(mind, "a cold wave on jagged rocks", ["threat"])
    mind.sleep()
    path = tmp_path / "aria.json"
    mind.save(str(path))
    reborn = Mind(settings=Settings())
    reborn.load(str(path))
    assert any("dream" in t.tags for t in reborn.memory.episodic)  # the dream is remembered
