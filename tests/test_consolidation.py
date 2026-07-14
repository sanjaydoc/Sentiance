"""Reflection / consolidation ("sleep") — distilling beliefs and resting."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind, Stimulus
from sentiance.mind.consolidation import consolidate
from sentiance.mind.memory import Memory
from sentiance.mind.state import AffectState, ConsciousMoment, ContentSource, Emotion


def _store(mem: Memory, content: str, emotion: Emotion, valence: float, tick: int) -> None:
    mem.store(
        ConsciousMoment(
            tick=tick,
            content=content,
            source=ContentSource.PERCEPT,
            salience=0.6,
            affect=AffectState(valence=valence, arousal=0.6, emotion=emotion),
            attention_target=content,
        ),
        tags=[],
    )


def test_recurring_pattern_becomes_a_belief() -> None:
    mem = Memory()
    _store(mem, "a loud crash startles me", Emotion.FEAR, -0.7, 1)
    _store(mem, "a loud bang in the crash of noise", Emotion.FEAR, -0.6, 2)
    beliefs = consolidate(mem)
    # "loud" and "crash" recur under fear → a belief about them.
    assert any("loud" in b or "crash" in b for b in beliefs)
    assert any(b.endswith("fear") for b in beliefs)


def test_one_off_does_not_become_a_belief() -> None:
    mem = Memory()
    _store(mem, "a single unremarkable event", Emotion.JOY, 0.4, 1)
    assert consolidate(mem) == []  # no recurrence → no belief


def test_sleep_forms_beliefs_calms_and_persists(tmp_path) -> None:
    mind = Mind(settings=Settings())
    for _ in range(3):
        mind.perceive(Stimulus(content="a loud crash", intensity=0.9, tags=["threat"]))
    mind.perceive(Stimulus(content="a loud crash again", intensity=0.9, tags=["threat"]))

    before_arousal = mind.affect.arousal
    added = mind.sleep()
    assert added  # she distilled at least one belief
    assert mind.state().beliefs
    assert mind.affect.arousal < before_arousal  # rested — calmer afterward

    path = tmp_path / "aria.json"
    mind.save(str(path))
    reborn = Mind(settings=Settings())
    reborn.load(str(path))
    assert reborn.state().beliefs == mind.state().beliefs  # beliefs endure
