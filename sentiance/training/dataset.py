"""Turn ``traces.jsonl`` into chat-formatted fine-tuning examples.

Each trace row is ``{system, prompt, thought, state, agent}`` (see
``sentiance.trace``). Here we keep only what a model needs to learn the *voice* —
the ``(system, prompt) → thought`` mapping — as chat messages, with light cleaning
(drop empties and trivially short thoughts, de-duplicate identical pairs), then a
deterministic train/val split. Pure Python: no torch, no transformers.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip(" .!?,\"'")


def _token_set(text: str) -> frozenset[str]:
    return frozenset(re.findall(r"[a-z']+", text.lower()))


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def load_traces(path: str | Path) -> list[dict]:
    """Read a JSONL trace file into a list of rows (skips blank/broken lines)."""
    rows: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    return rows


def to_chat_example(row: dict, *, include_state: bool = False) -> dict | None:
    """A trace row → an OpenAI-style chat example, or None if unusable.

    With ``include_state``, attach the numeric ``m_t`` vector (``state``) for the
    **fused** trainer — a row missing ``state_vec`` (an older Path-A trace) is
    dropped, since it can't condition the transformer."""
    system = (row.get("system") or "").strip()
    prompt = (row.get("prompt") or "").strip()
    thought = (row.get("thought") or "").strip()
    if not prompt or not thought:
        return None
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    messages.append({"role": "assistant", "content": thought})
    example: dict = {"messages": messages}
    if include_state:
        state_vec = row.get("state_vec")
        if not isinstance(state_vec, list) or not state_vec:
            return None
        example["state"] = [float(x) for x in state_vec]
    return example


def build_examples(
    rows: list[dict],
    *,
    agent: str | None = None,
    min_thought_words: int = 3,
    dedup: bool = True,
    similar_threshold: float = 0.85,
    window: int = 300,
    include_state: bool = False,
) -> list[dict]:
    """Clean trace rows into chat examples: drop empties / trivially short
    thoughts, exact duplicates, and — the important one for conversation data —
    **near**-duplicate thoughts (minds echoing each other), so the trained model
    doesn't learn to parrot. ``similar_threshold`` is the token-overlap (Jaccard)
    above which a thought counts as a near-echo of a recent one; set it to 1.0 to
    keep only exact-duplicate filtering.

    Pass ``agent`` (e.g. ``"Cass"``) to keep only *that* mind's deliberations —
    training on one consistent character gives a single, coherent voice; leaving
    it ``None`` blends everyone into a general Sentiance voice."""
    want = agent.lower() if agent else None
    examples: list[dict] = []
    seen_norm: set[str] = set()
    recent: list[frozenset[str]] = []
    for row in rows:
        if want is not None and (row.get("agent") or "").lower() != want:
            continue
        thought = (row.get("thought") or "").strip()
        if len(thought.split()) < min_thought_words:
            continue
        example = to_chat_example(row, include_state=include_state)
        if example is None:
            continue
        if dedup:
            norm = _norm(thought)
            if norm in seen_norm:
                continue
            tokens = _token_set(thought)
            if similar_threshold < 1.0 and any(
                _jaccard(tokens, prev) >= similar_threshold for prev in recent[-window:]
            ):
                continue
            seen_norm.add(norm)
            recent.append(tokens)
        examples.append(example)
    return examples


def split(examples: list[dict], val_frac: float = 0.1, seed: int = 0) -> tuple[list, list]:
    """Deterministic shuffle + train/val split."""
    shuffled = list(examples)
    random.Random(seed).shuffle(shuffled)
    n_val = max(1, int(len(shuffled) * val_frac)) if len(shuffled) > 10 else 0
    return shuffled[n_val:], shuffled[:n_val]


def write_jsonl(examples: list[dict], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")


def agent_counts(rows: list[dict]) -> dict[str, int]:
    """How many trace rows each named mind produced — so you can see who has
    enough data to train a single-character model."""
    counts: dict[str, int] = {}
    for row in rows:
        name = row.get("agent") or "?"
        counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))


def prepare(
    traces_path: str | Path,
    out_dir: str | Path = "data",
    *,
    agent: str | None = None,
    min_thought_words: int = 3,
    similar_threshold: float = 0.85,
    val_frac: float = 0.1,
    seed: int = 0,
    include_state: bool = False,
) -> dict:
    """Full pipeline: traces → cleaned examples → train/val files. Returns stats.

    ``include_state=True`` builds the **fused** dataset — each example keeps its
    numeric ``m_t`` (``state``) so a cognition-conditioned transformer can be
    trained on it (ADR 0005). Rows lacking a ``state_vec`` are dropped."""
    rows = load_traces(traces_path)
    examples = build_examples(
        rows, agent=agent, min_thought_words=min_thought_words,
        similar_threshold=similar_threshold, include_state=include_state,
    )
    train, val = split(examples, val_frac=val_frac, seed=seed)
    out = Path(out_dir)
    write_jsonl(train, out / "train.jsonl")
    if val:
        write_jsonl(val, out / "val.jsonl")
    return {
        "rows": len(rows),
        "examples": len(examples),
        "train": len(train),
        "val": len(val),
        "by_agent": agent_counts(rows),
        "agent": agent,
        "fused": include_state,
    }
