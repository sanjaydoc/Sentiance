"""A predictive world-model: the mind's expectation of what is normal.

Per predictive-processing accounts (Friston, Clark), a mind is fundamentally a
prediction machine; what it *feels* is tied to prediction error. This model is
deliberately simple — token familiarity — but it delivers the one signal the
rest of the architecture needs: **surprise** (novelty), which drives arousal and
the appraisal of what is worth becoming conscious of.
"""

from __future__ import annotations

from collections import Counter

from sentiance.mind.util import clamp, tokenize


class WorldModel:
    def __init__(self, smoothing: float = 1.0) -> None:
        self._counts: Counter[str] = Counter()
        self._observations = 0
        self._smoothing = smoothing

    def surprise(self, content: str, tags: list[str]) -> float:
        """Prediction error in [0, 1]: how unexpected these tokens are."""
        tokens = self._tokens(content, tags)
        if not tokens:
            return 0.5
        familiarities = [self._familiarity(tok) for tok in tokens]
        return clamp(1.0 - sum(familiarities) / len(familiarities))

    def update(self, content: str, tags: list[str]) -> None:
        for tok in self._tokens(content, tags):
            self._counts[tok] += 1
        self._observations += 1

    def dump(self) -> dict:
        return {"counts": dict(self._counts), "observations": self._observations}

    def load(self, data: dict) -> None:
        self._counts = Counter(data.get("counts", {}))
        self._observations = int(data.get("observations", 0))

    # --- internals --------------------------------------------------------

    def _familiarity(self, token: str) -> float:
        # Laplace-smoothed frequency → 0 (never seen) .. →1 (very familiar).
        count = self._counts[token]
        return count / (count + self._smoothing)

    @staticmethod
    def _tokens(content: str, tags: list[str]) -> list[str]:
        return tokenize(content) + [t.lower() for t in tags]
