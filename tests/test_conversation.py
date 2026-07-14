"""Conversational memory — remembering and picking up what others said."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind import Mind
from sentiance.mind.conversation import SAYS_RE, Conversation
from sentiance.mind.state import Stimulus


def test_says_pattern_parses_speaker_and_line() -> None:
    m = SAYS_RE.search("@Iris, beaming, says: I love the cherry blossoms")
    assert m is not None
    assert m.group(1) == "Iris"
    assert m.group(2) == "I love the cherry blossoms"
    assert SAYS_RE.search("@Milo and I meet — we share a warm handshake") is None


def test_conversation_keeps_recent_lines_per_person() -> None:
    c = Conversation(span=3)
    for line in ["one", "two", "three", "four"]:
        c.heard("Sam", line)
    assert c.last("Sam") == "four"
    assert c.recent("Sam", 2) == ["three", "four"]  # bounded, most-recent
    assert c.last("Nobody") is None


def test_a_mind_remembers_what_a_companion_said() -> None:
    mind = Mind(settings=Settings())
    mind.perceive(Stimulus(content="@Sam says: I love the blooming garden", intensity=0.6))
    assert mind.conversation.last("Sam") == "I love the blooming garden"
    assert mind.state().heard == "I love the blooming garden"  # in view for her next thought


def test_she_picks_up_the_topic_they_raised() -> None:
    mind = Mind(settings=Settings())  # offline voice
    mind.perceive(Stimulus(content="@Sam says: I love the blooming garden", intensity=0.6))
    thought = mind.think()
    assert thought is not None
    assert "garden" in thought.content  # her reply takes up what he raised, not a fresh tangent


def test_only_others_speech_is_remembered_not_her_own() -> None:
    mind = Mind(settings=Settings(agent_name="Iris"))
    # A line she "hears" that is attributed to herself must not be recorded.
    mind.perceive(Stimulus(content="@Iris says: I am thinking aloud", intensity=0.5))
    assert mind.conversation.last("Iris") is None


def test_housemates_reference_what_each_other_said() -> None:
    from sentiance.society import Society, _cast

    society = Society(_cast())
    referenced = False
    for _ in range(16):
        for _who, _affect, _perceived, _notes in society.step():
            pass
        if any(
            i.last_utterance and "pick up what they said" in i.last_utterance
            for i in society.inhabitants
        ):
            referenced = True
    assert referenced  # the conversation builds on itself, not just circling


def test_conversation_memory_persists(tmp_path) -> None:
    mind = Mind(settings=Settings())
    mind.perceive(Stimulus(content="@Sam says: the storm is passing", intensity=0.6))
    path = tmp_path / "aria.json"
    mind.save(str(path))
    reborn = Mind(settings=Settings())
    reborn.load(str(path))
    assert reborn.conversation.last("Sam") == "the storm is passing"
