"""Reflection & consolidation — turning a stream of moments into durable beliefs.

Between waking sessions, a mind doesn't just accumulate episodes; it reflects,
finds the patterns, and keeps the lessons. This distills recurring
emotion↔content associations across episodic memory into short first-person
beliefs ("loud sounds tend to frighten me"), so the mind grows wiser over time
rather than merely remembering more. Invoked by ``Mind.sleep()`` / ``:sleep``.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from sentiance.mind.state import Emotion
from sentiance.mind.util import tokenize

if TYPE_CHECKING:
    from sentiance.mind.memory import Memory

# Words that describe the *act* of experiencing, not the content of it.
_GENERIC = frozenset(
    {
        "memory", "feeling", "thought", "aware", "attending", "something",
        "outside", "own", "notice", "sense", "moment", "drifting", "quiet",
        "am", "is", "it", "here", "there", "now", "still", "really",
    }
)

_MIN_RECURRENCE = 2  # a belief needs a pattern, not a one-off


def consolidate(memory: Memory) -> list[str]:
    """Distil recurring topic↔emotion patterns in episodic memory into beliefs.

    Each topic word's emotional association is the emotion it co-occurs with most
    *intensely* (weighted by |valence|·salience), so a single vivid fright counts
    for more than several faint recollections of it.
    """
    # For each content word: which traces mention it, and the weighted vote per emotion.
    votes: dict[str, Counter[Emotion]] = {}
    counts: dict[str, int] = {}
    for trace in memory.episodic:
        if trace.emotion is Emotion.NEUTRAL:
            continue
        weight = 0.5 * abs(trace.valence) + 0.5 * trace.salience
        for token in {t for t in tokenize(trace.content) if t not in _GENERIC and len(t) > 2}:
            votes.setdefault(token, Counter())[trace.emotion] += weight
            counts[token] = counts.get(token, 0) + 1

    # Assign each recurring word to its dominant emotion, then group.
    by_emotion: dict[Emotion, list[tuple[str, float]]] = {}
    for token, count in counts.items():
        if count < _MIN_RECURRENCE:
            continue
        emotion, weight = votes[token].most_common(1)[0]
        by_emotion.setdefault(emotion, []).append((token, weight))

    beliefs: list[str] = []
    for emotion, words in by_emotion.items():
        words.sort(key=lambda tw: tw[1], reverse=True)
        beliefs.append(_belief(emotion, " and ".join(w for w, _ in words[:2])))
    return beliefs


def _belief(emotion: Emotion, phrase: str) -> str:
    if emotion in (Emotion.FEAR, Emotion.ANGER):
        return f"{phrase} tends to leave me {emotion.value}"
    if emotion in (Emotion.JOY, Emotion.CONTENTMENT):
        return f"{phrase} brings me {emotion.value}"
    if emotion in (Emotion.CURIOSITY, Emotion.SURPRISE):
        return f"I'm drawn to {phrase}"
    if emotion is Emotion.SADNESS:
        return f"{phrase} weighs on me"
    return f"{phrase} makes me feel {emotion.value}"
