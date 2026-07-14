"""Associative (semantic) memory — recall by meaning, with graceful fallback."""

from __future__ import annotations

from sentiance.core.config import Settings
from sentiance.mind.embeddings import build_embedder, cosine
from sentiance.mind.memory import Memory
from sentiance.mind.state import AffectState, ConsciousMoment, ContentSource, Emotion


class _FakeEmbedder:
    """Maps text to a small vector over hand-picked concepts, so that related
    words ("crash"/"bang"/"loud") land near each other — no server needed."""

    _CONCEPTS = ("loud", "calm", "person")
    _SYNONYMS = {
        "crash": "loud", "bang": "loud", "slam": "loud", "shout": "loud",
        "quiet": "calm", "gentle": "calm", "soft": "calm", "peace": "calm",
        "friend": "person", "voice": "person", "someone": "person",
    }

    def embed(self, text: str) -> list[float] | None:
        vec = [0.01, 0.01, 0.01]
        for word in text.lower().split():
            concept = self._SYNONYMS.get(word.strip(".,!?"))
            if concept:
                vec[self._CONCEPTS.index(concept)] += 1.0
        return vec


def _moment(content: str, tick: int) -> ConsciousMoment:
    return ConsciousMoment(
        tick=tick,
        content=content,
        source=ContentSource.PERCEPT,
        salience=0.6,
        affect=AffectState(valence=-0.3, arousal=0.6, emotion=Emotion.FEAR),
        attention_target=content,
    )


def test_cosine_basic() -> None:
    assert cosine([1, 0], [1, 0]) == 1.0
    assert cosine([1, 0], [0, 1]) == 0.0


def test_semantic_recall_finds_related_meaning_not_shared_words() -> None:
    mem = Memory(embedder=_FakeEmbedder())
    mem.store(_moment("a loud crash", 1), tags=["threat"])
    mem.store(_moment("a gentle breeze", 2), tags=["calm"])

    # "bang" shares NO words with "a loud crash" — lexical recall would miss it.
    recalled = mem.retrieve("a sudden bang", [], k=1)
    assert recalled
    assert "crash" in recalled[0].content  # found by meaning


def test_falls_back_to_lexical_when_embedder_returns_none() -> None:
    class _DeadEmbedder:
        def embed(self, text: str) -> list[float] | None:
            return None

    mem = Memory(embedder=_DeadEmbedder())
    mem.store(_moment("a loud crash", 1), tags=["threat"])
    # Lexical fallback still recalls on the shared word "crash".
    recalled = mem.retrieve("another crash nearby", [], k=1)
    assert recalled
    assert "crash" in recalled[0].content


def test_build_embedder_selects_backend() -> None:
    assert build_embedder(Settings(embedding_backend="none")) is None
    assert build_embedder(Settings(embedding_backend="ollama")) is not None
