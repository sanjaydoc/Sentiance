"""Unit tests for the sentiment analyzer."""

from __future__ import annotations

import pytest

from app.schemas import Sentiment
from app.sentiment import SentimentAnalyzer


@pytest.fixture
def analyzer() -> SentimentAnalyzer:
    return SentimentAnalyzer()


def test_positive_text(analyzer: SentimentAnalyzer) -> None:
    result = analyzer.analyze("I love this, it is great and wonderful!")
    assert result.sentiment is Sentiment.POSITIVE
    assert result.score > 0


def test_negative_text(analyzer: SentimentAnalyzer) -> None:
    result = analyzer.analyze("This is terrible, awful and I hate it.")
    assert result.sentiment is Sentiment.NEGATIVE
    assert result.score < 0


def test_neutral_text(analyzer: SentimentAnalyzer) -> None:
    result = analyzer.analyze("The package arrived on Tuesday.")
    assert result.sentiment is Sentiment.NEUTRAL
    assert result.score == 0.0


def test_negation_flips_sentiment(analyzer: SentimentAnalyzer) -> None:
    result = analyzer.analyze("This is not good.")
    assert result.sentiment is Sentiment.NEGATIVE
    assert result.score < 0


def test_score_bounds(analyzer: SentimentAnalyzer) -> None:
    result = analyzer.analyze("great great great great great great great great")
    assert -1.0 <= result.score <= 1.0
