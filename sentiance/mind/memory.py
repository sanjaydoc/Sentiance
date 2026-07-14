"""Memory: working, episodic, and semantic.

- **Working memory** holds the last few conscious contents (Miller's 7±2).
- **Episodic memory** lays down each conscious moment with its affective charge;
  emotionally intense moments are recalled more readily (mood-congruent, salience-
  weighted retrieval).
- **Semantic memory** accumulates token co-occurrence — a crude associative web.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import TYPE_CHECKING

from sentiance.mind.embeddings import cosine
from sentiance.mind.state import Candidate, ConsciousMoment, ContentSource, MemoryTrace
from sentiance.mind.util import clamp, strip_narration, tokenize

if TYPE_CHECKING:
    from sentiance.mind.embeddings import Embedder


class Memory:
    def __init__(
        self,
        working_size: int = 7,
        episodic_capacity: int = 500,
        embedder: Embedder | None = None,
    ) -> None:
        self.working: deque[str] = deque(maxlen=working_size)
        self.episodic: deque[MemoryTrace] = deque(maxlen=episodic_capacity)
        self.semantic: dict[str, Counter[str]] = {}
        self.embedder = embedder
        self._vectors: dict[str, list[float]] = {}  # trace_id → embedding (not persisted)

    def store(self, moment: ConsciousMoment, tags: list[str]) -> None:
        # Store the underlying content, not the act of recalling it, so replayed
        # memories don't nest into "a memory: a memory: …".
        base = strip_narration(moment.content)
        self.working.append(base)
        trace = MemoryTrace(
            tick=moment.tick,
            content=base,
            tags=tags,
            emotion=moment.affect.emotion,
            valence=moment.affect.valence,
            salience=moment.salience,
        )
        self.episodic.append(trace)
        self._index(base, tags)
        if self.embedder is not None:
            self._vector_for(trace)  # embed now while the content is fresh

    def retrieve(self, cue: str, tags: list[str], k: int = 1) -> list[Candidate]:
        """Recall episodes associated with the cue, as MEMORY candidates.

        Uses embedding similarity (recall by *meaning*) when an embedder is
        configured, falling back to token overlap otherwise.
        """
        if self.embedder is not None:
            semantic = self._retrieve_semantic(cue, tags, k)
            if semantic is not None:
                return semantic
        return self._retrieve_lexical(cue, tags, k)

    def _retrieve_lexical(self, cue: str, tags: list[str], k: int) -> list[Candidate]:
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
        return self._as_candidates(scored[:k])

    def _retrieve_semantic(self, cue: str, tags: list[str], k: int) -> list[Candidate] | None:
        assert self.embedder is not None
        query = self.embedder.embed(cue if not tags else f"{cue} {' '.join(tags)}")
        if query is None:
            return None  # embedder unavailable → let the caller fall back to lexical
        scored: list[tuple[float, MemoryTrace]] = []
        for trace in self.episodic:
            vector = self._vector_for(trace)
            if vector is None:
                continue
            sim = cosine(query, vector)
            if sim <= 0.15:  # unrelated — don't surface noise
                continue
            score = sim * (0.5 + 0.5 * trace.salience + 0.3 * abs(trace.valence))
            scored.append((score, trace))
        if not scored:
            return None
        scored.sort(key=lambda st: st[0], reverse=True)
        return self._as_candidates(scored[:k])

    def _as_candidates(self, scored: list[tuple[float, MemoryTrace]]) -> list[Candidate]:
        return [
            Candidate(
                content=f"a memory: {trace.content}",
                source=ContentSource.MEMORY,
                salience=clamp(0.2 + 0.15 * score),
            )
            for score, trace in scored
        ]

    def _vector_for(self, trace: MemoryTrace) -> list[float] | None:
        """Cached embedding for a trace (embedded lazily; recomputed after load)."""
        if trace.trace_id in self._vectors:
            return self._vectors[trace.trace_id]
        if self.embedder is None:
            return None
        vector = self.embedder.embed(trace.content)
        if vector is not None:
            self._vectors[trace.trace_id] = vector
        return vector

    def dump(self) -> dict:
        return {
            "working": list(self.working),
            "episodic": [t.model_dump() for t in self.episodic],
            "semantic": {tok: dict(bag) for tok, bag in self.semantic.items()},
        }

    def load(self, data: dict) -> None:
        self.working = deque(data.get("working", []), maxlen=self.working.maxlen)
        self.episodic = deque(
            (MemoryTrace(**t) for t in data.get("episodic", [])), maxlen=self.episodic.maxlen
        )
        self.semantic = {tok: Counter(bag) for tok, bag in data.get("semantic", {}).items()}

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
