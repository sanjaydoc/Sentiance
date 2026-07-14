"""End-to-end tests of the cognitive cycle."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind, Stimulus
from sentiance.mind.state import ContentSource, Emotion


def test_tick_returns_moment_and_report(mind: Mind) -> None:
    result = mind.perceive(Stimulus(content="a gentle light", intensity=0.5, tags=["light"]))
    assert result.moment.tick == 1
    assert result.report.tick == 1
    assert result.report.text.startswith("I am aware")
    assert 0.0 <= result.report.confidence <= 1.0


def test_threat_makes_the_mind_afraid(mind: Mind) -> None:
    result = mind.perceive(
        Stimulus(content="a loud crash in the dark", intensity=0.95, tags=["threat", "alarm"])
    )
    assert result.moment.affect.valence < 0
    assert result.moment.affect.emotion in (Emotion.FEAR, Emotion.ANGER)


def test_memories_resurface_later(mind: Mind) -> None:
    mind.perceive(Stimulus(content="a friendly voice says hello", intensity=0.6, tags=["friend"]))
    mind.perceive(Stimulus(content="a loud crash", intensity=0.95, tags=["threat"]))
    # Idle: the friendly voice should be recallable as a memory.
    seen_memory = False
    for _ in range(4):
        r = mind.idle()
        if r.moment.source is ContentSource.MEMORY or "memory" in r.moment.content:
            seen_memory = True
    assert seen_memory


def test_emotion_carries_over_then_eases(mind: Mind) -> None:
    # A frightening event should stay negative through the mind's own reflection
    # (not snap back to neutral/positive), then gradually ease.
    r = mind.perceive(
        Stimulus(content="a sudden loud crash", intensity=0.95, tags=["threat", "alarm"])
    )
    assert r.moment.affect.valence < -0.3  # genuinely afraid

    first = mind.idle().moment.affect.valence
    assert first < 0.0  # the feeling carried over into the inner thought, not reset

    tail = [mind.idle().moment.affect.valence for _ in range(6)][-1]
    assert tail > first  # ...and it eased back up over the following ticks


def test_self_model_tracks_state(mind: Mind) -> None:
    mind.perceive(Stimulus(content="a warm greeting", intensity=0.6, tags=["friend"]))
    state = mind.state()
    assert state.name == "Aria"
    assert state.tick == 1
    assert state.drives  # populated
    assert "→" in state.narrative or state.narrative


def test_mind_wanders_without_input(mind: Mind) -> None:
    # With no stimuli at all, the mind still produces an inner stream.
    results = [mind.idle() for _ in range(3)]
    assert len(results) == 3
    assert all(r.moment.content for r in results)


def test_cycle_is_deterministic() -> None:
    stimuli = [
        Stimulus(content="a soft chime", intensity=0.5, tags=["sound"]),
        Stimulus(content="a loud crash", intensity=0.9, tags=["threat"]),
    ]
    a = Mind(settings=Settings()).live(stimuli, idle_after=3)
    b = Mind(settings=Settings()).live(stimuli, idle_after=3)
    assert [r.moment.content for r in a] == [r.moment.content for r in b]
    assert [r.moment.affect.emotion for r in a] == [r.moment.affect.emotion for r in b]


def test_broadcast_reaches_external_subscriber() -> None:
    mind = Mind(settings=Settings())
    received: list = []
    mind.workspace.subscribe_conscious(received.append)
    mind.perceive(Stimulus(content="a new idea", intensity=0.6, tags=["idea"]))
    assert len(received) == 1
    assert received[0].tick == 1
