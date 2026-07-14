"""Dreaming — offline recombination of memory during sleep.

Consolidation distils what happened into sober beliefs. Dreaming does the
stranger, more generative thing: it takes fragments of the day's most charged
episodes and **weaves them into something that never happened** — a short,
surreal sequence carrying a blended feeling. Stitching pieces of *different*
memories together forges associations she never made while awake, so she can wake
subtly changed: new links between ideas, and — if the dream ran hot — a fresh
intention to make sense of it.

A functional correlate of dreaming as generative memory replay (Hobson;
Wamsley) — recombination, not prophecy; no claim the dream is experienced.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sentiance.mind.state import Emotion
from sentiance.mind.util import strip_narration

if TYPE_CHECKING:
    from sentiance.mind.memory import Memory


@dataclass
class Dream:
    fragments: list[str]  # the memory pieces it wove together
    narrative: str  # the surreal retelling
    tone: float  # blended feeling of the dream
    emotion: Emotion


def dream(memory: Memory, tick: int, fragments: int = 3) -> Dream | None:
    """Weave a dream from the most charged episodes in memory, or None if there's
    too little to dream on. Deterministic in ``tick`` (no randomness), so a given
    night's dream is reproducible."""
    pool = [
        t
        for t in memory.episodic
        if t.emotion is not Emotion.NEUTRAL and "dream" not in t.tags
    ]
    if len(pool) < 2:
        return None
    pool.sort(key=lambda t: t.salience + 0.4 * abs(t.valence), reverse=True)
    top = pool[: max(fragments + 2, 5)]
    picks = [top[i] for i in _spread(len(top), fragments, tick)]

    frags = [strip_narration(t.content) for t in picks]
    tone = round(sum(t.valence for t in picks) / len(picks), 3)
    emotion = _dominant(picks)
    return Dream(fragments=frags, narrative=_weave(frags, tone), tone=tone, emotion=emotion)


def _spread(m: int, n: int, tick: int) -> list[int]:
    """Pick up to ``n`` distinct indices from ``range(m)``, spaced out and shifted
    by ``tick`` so successive nights recombine different fragments."""
    if m <= n:
        return list(range(m))
    step = max(1, m // n)
    idxs: list[int] = []
    for i in range(n):
        cand = (tick + i * step) % m
        while cand in idxs:
            cand = (cand + 1) % m
        idxs.append(cand)
    return idxs


def _dominant(picks: list) -> Emotion:
    tally: Counter[Emotion] = Counter()
    for t in picks:
        tally[t.emotion] += 0.5 + 0.5 * abs(t.valence)
    return tally.most_common(1)[0][0]


def _weave(frags: list[str], tone: float) -> str:
    joiner = " and then it became " if tone >= 0 else " but it twisted into "
    text = "I dreamt of " + frags[0]
    for frag in frags[1:]:
        text += joiner + frag
    return text + "."
