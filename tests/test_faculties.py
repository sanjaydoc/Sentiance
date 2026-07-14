"""Unit tests for the individual faculties."""

from __future__ import annotations

from sentiance.mind.affect import AffectSystem
from sentiance.mind.attention import AttentionSystem
from sentiance.mind.drives import Drives
from sentiance.mind.memory import Memory
from sentiance.mind.perception import Perceptor
from sentiance.mind.state import (
    AffectState,
    Appraisal,
    Candidate,
    ConsciousMoment,
    ContentSource,
    Emotion,
    Percept,
    Stimulus,
)
from sentiance.mind.util import strip_narration
from sentiance.mind.world_model import WorldModel


def test_world_model_familiarity_reduces_surprise() -> None:
    w = WorldModel()
    first = w.surprise("a bright red apple", [])
    for _ in range(5):
        w.update("a bright red apple", [])
    later = w.surprise("a bright red apple", [])
    assert later < first


def test_perceptor_novelty_and_salience() -> None:
    w = WorldModel()
    p = Perceptor().perceive(Stimulus(content="an unheard word", intensity=0.8), w)
    assert 0.0 <= p.salience <= 1.0
    assert p.novelty > 0.5  # never seen → surprising


def test_threat_produces_fear() -> None:
    percept = Percept(
        content="a loud crash", tags=["threat"], intensity=0.95, novelty=0.9, salience=0.9
    )
    appraisal, _drive = Drives().appraise(percept)
    affect = AffectSystem().appraise(percept, appraisal, AffectState())
    assert affect.valence < 0
    assert affect.arousal > 0.5
    assert affect.emotion in (Emotion.FEAR, Emotion.ANGER)


def test_pleasant_social_is_positive() -> None:
    percept = Percept(
        content="a friend greets me", tags=["friend"], intensity=0.6, novelty=0.5, salience=0.6
    )
    appraisal, _drive = Drives().appraise(percept)
    affect = AffectSystem().appraise(percept, appraisal, AffectState())
    assert affect.valence > 0


def test_affect_labels_cover_circumplex() -> None:
    a = AffectSystem()
    good = Appraisal(novelty=0.1, goal_congruence=0.5, control=0.9, relevance=0.5)
    assert a._label(0.5, 0.2, good) is Emotion.CONTENTMENT
    assert a._label(0.5, 0.8, good) is Emotion.JOY


def test_attention_selects_highest_salience() -> None:
    cands = [
        Candidate(content="dim", source=ContentSource.PERCEPT, salience=0.2),
        Candidate(content="bright", source=ContentSource.FEELING, salience=0.9),
    ]
    winner, also = AttentionSystem().select(cands, arousal=0.5)
    assert winner.content == "bright"
    assert len(also) == 1


def test_memory_store_and_retrieve_without_nesting() -> None:
    mem = Memory()
    moment = ConsciousMoment(
        tick=1,
        content="a memory: a soft chime",
        source=ContentSource.MEMORY,
        salience=0.8,
        affect=AffectState(valence=0.3, arousal=0.4),
        attention_target="a memory: a soft chime",
    )
    mem.store(moment, tags=["sound"])
    # The stored trace is the underlying content, not the recall wrapper.
    assert mem.episodic[0].content == "a soft chime"
    recalled = mem.retrieve("chime", ["sound"], k=1)
    assert recalled
    assert strip_narration(recalled[0].content) == "a soft chime"


def test_memory_most_salient() -> None:
    mem = Memory()
    for i, (content, sal) in enumerate([("quiet", 0.2), ("vivid", 0.9)], start=1):
        mem.store(
            ConsciousMoment(
                tick=i,
                content=content,
                source=ContentSource.PERCEPT,
                salience=sal,
                affect=AffectState(),
                attention_target=content,
            ),
            tags=[],
        )
    assert mem.most_salient().content == "vivid"
