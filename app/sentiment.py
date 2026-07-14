"""A small, dependency-free lexicon-based sentiment analyzer.

This keeps the scaffold self-contained and fast to test. Swap the
``SentimentAnalyzer`` implementation for a real model (e.g. a transformer or a
hosted API) without changing the API layer.
"""

from __future__ import annotations

import re

from app.schemas import AnalyzeResponse, Sentiment

_POSITIVE_WORDS = frozenset(
    {
        "good", "great", "excellent", "amazing", "wonderful", "love", "loved",
        "like", "happy", "fantastic", "awesome", "best", "nice", "delightful",
        "pleased", "positive", "brilliant", "superb", "perfect", "enjoy",
    }
)

_NEGATIVE_WORDS = frozenset(
    {
        "bad", "terrible", "awful", "horrible", "hate", "hated", "dislike",
        "sad", "worst", "poor", "disappointing", "disappointed", "negative",
        "broken", "ugly", "boring", "annoying", "angry", "wrong", "useless",
    }
)

_NEGATIONS = frozenset({"not", "no", "never", "n't", "cannot", "without"})

_TOKEN_RE = re.compile(r"[a-zA-Z']+")


class SentimentAnalyzer:
    """Score text polarity using a simple word lexicon with negation handling."""

    def analyze(self, text: str) -> AnalyzeResponse:
        tokens = _TOKEN_RE.findall(text.lower())
        score = 0
        negate = False

        for token in tokens:
            if token in _NEGATIONS:
                negate = True
                continue

            weight = 0
            if token in _POSITIVE_WORDS:
                weight = 1
            elif token in _NEGATIVE_WORDS:
                weight = -1

            if weight:
                score += -weight if negate else weight

            # Negation only affects the next sentiment-bearing word.
            if weight or token in _NEGATIONS:
                negate = False

        normalized = _normalize(score, len(tokens))
        return AnalyzeResponse(
            text=text,
            sentiment=_label(normalized),
            score=round(normalized, 4),
        )


def _normalize(score: int, token_count: int) -> float:
    if token_count == 0 or score == 0:
        return 0.0
    # Squash into [-1, 1] using the raw score; longer texts don't over-saturate.
    magnitude = min(abs(score), 5) / 5.0
    return magnitude if score > 0 else -magnitude


def _label(score: float) -> Sentiment:
    if score > 0.05:
        return Sentiment.POSITIVE
    if score < -0.05:
        return Sentiment.NEGATIVE
    return Sentiment.NEUTRAL


# Module-level singleton reused across requests.
analyzer = SentimentAnalyzer()
