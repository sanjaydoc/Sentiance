"""State-blind prompting — the fused mind gets its state only from m_t (ADR 0005)."""

from __future__ import annotations

from sentiance.mind.cognition import _compose_prompt
from sentiance.mind.state import AffectState, ContentSource, Drive, Emotion, SelfModelState
from sentiance.training.dataset import _strip_state, to_chat_example


def _snap() -> SelfModelState:
    return SelfModelState(
        name="Aria", tick=3, current_focus="x",
        affect=AffectState(valence=-0.6, arousal=0.7, emotion=Emotion.FEAR),
        drives={Drive.CURIOSITY: 0.5, Drive.COHERENCE: 0.5,
                Drive.SAFETY: 0.5, Drive.CONNECTION: 0.5},
        narrative="I heard a sound and went to look.",
        goals=["reach the far room"],
    )


def test_state_blind_prompt_omits_the_felt_state() -> None:
    _, full = _compose_prompt(_snap(), "a crash in the dark", ContentSource.PERCEPT)
    _, blind = _compose_prompt(_snap(), "a crash in the dark", ContentSource.PERCEPT,
                               state_blind=True)
    # the felt state is gone; the situation + narrative remain
    assert "I feel fear" in full and "My drives" in full
    assert "I feel" not in blind and "My drives" not in blind and "trying to do" not in blind
    assert "a crash in the dark" in blind
    assert "Recent stream: I heard a sound and went to look." in blind


def test_strip_state_rebuilds_the_blind_prompt_from_a_full_one() -> None:
    # so a fused dataset can be built from older traces that lack `prompt_blind`
    _, full = _compose_prompt(_snap(), "a crash in the dark", ContentSource.PERCEPT)
    _, blind = _compose_prompt(_snap(), "a crash in the dark", ContentSource.PERCEPT,
                               state_blind=True)
    assert _strip_state(full) == blind


def test_fused_example_uses_the_blind_prompt() -> None:
    row = {
        "system": "sys", "prompt": "FULL with I feel...", "prompt_blind": "BLIND situation only",
        "thought": "I should be careful here.", "state_vec": [0.0] * 41,
    }
    ex = to_chat_example(row, include_state=True, state_blind=True)
    assert ex is not None
    user = next(m["content"] for m in ex["messages"] if m["role"] == "user")
    assert user == "BLIND situation only"  # used prompt_blind, not the full prompt
    assert ex["state"] == [0.0] * 41
