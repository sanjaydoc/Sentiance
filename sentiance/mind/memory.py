"""Memory: working, episodic, and semantic.

- **Working memory** holds the last few conscious contents (Miller's 7±2).
- **Episodic memory** lays down each conscious moment with its affective charge;
  emotionally intense moments are recalled more readily (mood-congruent, salience-
  weighted retrieval).
- **Semantic memory** accumulates token co-occurrence — a crude associative web.
"""

from __future__ import annotations

from collections import Counter, deque

from sentiance.mind.state import Candidate, ConsciousMoment, ContentSource, MemoryTrace
from sentiance.mind.util import clamp, strip_narration, tokenize


class Memory:
    def __init__(self, working_size: int = 7, episodic_capacity: int = 500) -> None:
        self.working: deque[str] = deque(maxlen=working_size)
        self.episodic: deque[MemoryTrace] = deque(maxlen=episodic_capacity)
        self.semantic: dict[str, Counter[str]] = {}

    def store(self, moment: ConsciousMoment, tags: list[str]) -> None:
        # Store the underlying content, not the act of recalling it, so replayed
        # memories don't nest into "a memory: a memory: …".
        base = strip_narration(moment.content)
        self.working.append(base)
        self.episodic.append(
            MemoryTrace(
                tick=moment.tick,
                content=base,
                tags=tags,
                emotion=moment.affect.emotion,
                valence=moment.affect.valence,
                salience=moment.salience,
            )
        )
        self._index(base, tags)

    def retrieve(self, cue: str, tags: list[str], k: int = 1) -> list[Candidate]:
        """Recall episodes associated with the cue, as MEMORY candidates."""
        cue_tokens = set(tokenize(cue) + [t.lower() for t in tags])
        scored: list[tuple[float, MemoryTrace]] = []
        for trace in self.episodic:
            trace_tokens = set(tokenize(trace.content) + [t.lower() for t in trace.tags])
            overlap = len(cue_tokens & trace_tokens)
            if overlap == 0:
                continue
            # Salient + emotionally charged memories surface more strongly.
            score = overlap * (0.5 + 0.5 * trace.salience + 0.3 * abs(trace.valence))
            scored.append((score, trace))

        scored.sort(key=lambda st: st[0], reverse=True)
        out: list[Candidate] = []
        for score, trace in scored[:k]:
            out.append(
                Candidate(
                    content=f"a memory: {trace.content}",
                    source=ContentSource.MEMORY,
                    salience=clamp(0.2 + 0.15 * score),
                )
            )
        return out

    def most_salient(self) -> MemoryTrace | None:
        """The single most memorable episode (for mind-wandering)."""
        if not self.episodic:
            return None
        return max(
            self.episodic, key=lambda t: t.salience + 0.3 * abs(t.valence)
        )

    def associations(self, token: str, k: int = 3) -> list[str]:
        counter = self.semantic.get(token.lower())
        return [tok for tok, _ in counter.most_common(k)] if counter else []

    # --- internals --------------------------------------------------------

    def _index(self, content: str, tags: list[str]) -> None:
        tokens = tokenize(content) + [t.lower() for t in tags]
        for tok in tokens:
            bag = self.semantic.setdefault(tok, Counter())
            for other in tokens:
                if other != tok:
                    bag[other] += 1
