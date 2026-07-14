"""Small shared helpers for the faculties."""

from __future__ import annotations

import math
import re

_WORD_RE = re.compile(r"[a-z0-9']+")
_STOPWORDS = frozenset(
    {"the", "a", "an", "of", "to", "is", "it", "i", "my", "and", "in", "on", "at", "this"}
)


_NARRATION_PREFIXES = ("a memory:", "(drifting)", "(recalling)", "(remembering)", "(quiet)")


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def strip_narration(text: str) -> str:
    """Remove stacked recall/wander prefixes so memories don't nest endlessly."""
    changed = True
    while changed:
        changed = False
        stripped = text.lstrip()
        for prefix in _NARRATION_PREFIXES:
            if stripped.lower().startswith(prefix):
                text = stripped[len(prefix):].lstrip()
                changed = True
    return text


def tokenize(text: str) -> list[str]:
    """Content words of a piece of text (lowercased, stopwords removed)."""
    return [w for w in _WORD_RE.findall(text.lower()) if w not in _STOPWORDS]


def softmax(scores: list[float], temperature: float) -> list[float]:
    if not scores:
        return []
    t = max(temperature, 1e-3)
    m = max(scores)
    exps = [math.exp((s - m) / t) for s in scores]
    total = sum(exps)
    return [e / total for e in exps]
