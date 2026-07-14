"""Richer metacognition — varied phrasing and familiarity awareness."""

from __future__ import annotations

from sentiance.mind.metacognition import Metacognition
from sentiance.mind.state import (
    AffectState,
    Appraisal,
    ConsciousMoment,
    ContentSource,
    Drive,
    Emotion,
)


def _moment(tick: int) -> ConsciousMoment:
    return ConsciousMoment(
        tick=tick,
        content="a soft chime",
        source=ContentSource.PERCEPT,
        salience=0.6,
        affect=AffectState(valence=0.3, arousal=0.5, emotion=Emotion.JOY),
        attention_target="a soft chime",
    )


def _appraisal(novelty: float) -> Appraisal:
    return Appraisal(novelty=novelty, goal_congruence=0.4, control=0.7, relevance=0.5)


def _sm() -> object:
    from sentiance.mind.state import SelfModelState

    return SelfModelState(
        name="Aria",
        tick=1,
        current_focus="a soft chime",
        affect=AffectState(),
        drives={Drive.CURIOSITY: 0.5},
        narrative="",
    )


def test_reports_vary_across_ticks() -> None:
    meta = Metacognition()
    openers = {
        meta.reflect(_moment(t), _sm(), _appraisal(0.5), Drive.CURIOSITY).text[:20]
        for t in range(1, 5)
    }
    assert len(openers) > 1  # the inner voice isn't identical every moment


def test_tick_one_still_starts_conventionally() -> None:
    meta = Metacognition()
    text = meta.reflect(_moment(1), _sm(), _appraisal(0.5), Drive.CURIOSITY).text
    assert text.startswith("I am aware")


def test_novel_vs_familiar_phrasing() -> None:
    meta = Metacognition()
    novel = meta.reflect(_moment(1), _sm(), _appraisal(0.9), Drive.CURIOSITY).text
    familiar = meta.reflect(_moment(1), _sm(), _appraisal(0.1), Drive.CURIOSITY).text
    assert "new to me" in novel
    assert "familiar" in familiar


def test_novelty_decays_with_repetition() -> None:
    from sentiance.mind.world_model import WorldModel

    w = WorldModel()
    first = w.surprise("a soft chime", ["sound"])
    for _ in range(3):
        w.update("a soft chime", ["sound"])
    assert w.surprise("a soft chime", ["sound"]) < first - 0.2  # familiar faster now
