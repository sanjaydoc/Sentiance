"""The mind-state vector m_t and the per-faculty ``signals`` hook (ADR 0005)."""

from __future__ import annotations

from sentiance.mind import Mind, Stimulus
from sentiance.mind.state import AffectState, ContentSource, Drive, Emotion, SelfModelState
from sentiance.mind.state_vector import SIGNAL_FIELDS, STATE_DIM, STATE_FIELDS, encode_state


def _snap(**kw) -> SelfModelState:
    base = {
        "name": "Aria", "tick": 1, "current_focus": "x",
        "affect": AffectState(valence=0.5, arousal=0.4, emotion=Emotion.JOY),
        "drives": {Drive.CURIOSITY: 0.8, Drive.COHERENCE: 0.5,
                   Drive.SAFETY: 0.3, Drive.CONNECTION: 0.6},
        "narrative": "",
    }
    base.update(kw)
    return SelfModelState(**base)


def test_vector_is_fixed_length_and_named() -> None:
    vec = encode_state(_snap(), ContentSource.PERCEPT)
    assert len(vec) == STATE_DIM == len(STATE_FIELDS)
    assert all(isinstance(x, float) for x in vec)


def test_emotion_is_one_hot() -> None:
    vec = encode_state(_snap(affect=AffectState(emotion=Emotion.GRIEF)), ContentSource.FEELING)
    emotion_slice = [vec[STATE_FIELDS.index(f"emotion:{e.value}")] for e in Emotion]
    assert sum(emotion_slice) == 1.0
    assert vec[STATE_FIELDS.index("emotion:grief")] == 1.0


def test_source_and_drives_land_in_their_slots() -> None:
    vec = encode_state(_snap(), ContentSource.MEMORY)
    assert vec[STATE_FIELDS.index("source:memory")] == 1.0
    assert vec[STATE_FIELDS.index("source:percept")] == 0.0
    assert vec[STATE_FIELDS.index("drive:curiosity")] == 0.8


def test_signals_fold_in_by_name() -> None:
    signals = dict.fromkeys(SIGNAL_FIELDS, 0.0)
    signals["frustration"] = 0.7
    signals["anticipation"] = -1.0  # dread
    vec = encode_state(_snap(signals=signals, goals=["reach the far room"]), ContentSource.THOUGHT)
    assert vec[STATE_FIELDS.index("frustration")] == 0.7
    assert vec[STATE_FIELDS.index("anticipation")] == -1.0
    assert vec[STATE_FIELDS.index("has_goal")] == 1.0


def test_missing_signals_default_to_zero() -> None:
    # An older snapshot with no signals still encodes cleanly.
    vec = encode_state(_snap(), ContentSource.PERCEPT)
    for name in SIGNAL_FIELDS:
        assert vec[STATE_FIELDS.index(name)] == 0.0


def test_live_mind_exposes_signals_on_its_snapshot() -> None:
    mind = Mind()
    mind.perceive(Stimulus(content="a sudden loud crash", intensity=0.9, tags=["threat"]))
    snap = mind.state()
    # Every declared signal is present and numeric — the whole cycle is encodable.
    assert set(SIGNAL_FIELDS) <= set(snap.signals)
    assert all(isinstance(v, float) for v in snap.signals.values())
    vec = encode_state(snap, ContentSource.PERCEPT)
    assert len(vec) == STATE_DIM
