"""Attention: the competition that decides what becomes conscious.

Global Workspace Theory casts consciousness as the winner of a competition among
specialized processes for a limited broadcast capacity. Candidates (a percept, a
felt emotion, a recalled memory, a self-generated thought) compete by salience;
arousal sharpens the competition (a keyed-up mind fixates). The single winner is
what the mind becomes conscious *of*; the rest form the losing coalition.
"""

from __future__ import annotations

from sentiance.mind.state import Candidate
from sentiance.mind.util import clamp, softmax


class AttentionSystem:
    def __init__(self, temperature: float = 0.5) -> None:
        self.temperature = temperature

    def select(
        self, candidates: list[Candidate], arousal: float
    ) -> tuple[Candidate, list[Candidate]]:
        if not candidates:
            raise ValueError("attention needs at least one candidate")

        # Higher arousal → lower effective temperature → sharper focus.
        temp = clamp(self.temperature * (1.3 - 0.8 * arousal), 0.1, 2.0)
        weights = softmax([c.salience for c in candidates], temp)

        ranked = sorted(
            zip(candidates, weights, strict=True), key=lambda cw: cw[1], reverse=True
        )
        winner = ranked[0][0]
        # Report each candidate's post-competition activation as its salience.
        also = [c.model_copy(update={"salience": round(w, 4)}) for c, w in ranked[1:]]
        return winner, also
