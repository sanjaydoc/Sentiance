"""Path A — trace → dataset prep, and the finetuned backend's graceful fallback."""

from __future__ import annotations

import json

from sentiance.core.config import Settings
from sentiance.mind import Mind
from sentiance.mind.state import Stimulus
from sentiance.training.dataset import (
    build_examples,
    prepare,
    split,
    to_chat_example,
)


def test_a_trace_row_becomes_a_chat_example() -> None:
    ex = to_chat_example({"system": "S", "prompt": "P", "thought": "a real inner thought"})
    assert ex is not None
    assert [m["role"] for m in ex["messages"]] == ["system", "user", "assistant"]
    assert ex["messages"][-1]["content"] == "a real inner thought"


def test_unusable_rows_are_dropped() -> None:
    assert to_chat_example({"prompt": "", "thought": "x"}) is None
    assert to_chat_example({"prompt": "p", "thought": ""}) is None


def test_build_examples_filters_short_and_dedups() -> None:
    rows = [
        {"system": "S", "prompt": "P", "thought": "one two three"},
        {"system": "S", "prompt": "P", "thought": "one two three"},  # duplicate pair
        {"system": "S", "prompt": "Q", "thought": "hi"},  # too short
    ]
    examples = build_examples(rows, min_thought_words=3)
    assert len(examples) == 1  # one kept: the non-trivial, de-duplicated pair


def test_near_duplicate_echoes_are_dropped() -> None:
    # The parrot loop two minds fall into — nearly the same line over and over.
    echo = [
        "I should reach out to Milo and see how he is doing",
        "I should reach out to Iris and see how she is doing",
        "I should reach out to Milo and see how he is doing too",
        "I wonder what the garden looks like at dawn",  # genuinely different
    ]
    rows = [{"system": "S", "prompt": f"P{i}", "thought": t} for i, t in enumerate(echo)]
    kept = build_examples(rows, similar_threshold=0.6)
    thoughts = [e["messages"][-1]["content"] for e in kept]
    assert len(kept) < len(echo)  # the near-echoes are collapsed
    assert any("garden" in t for t in thoughts)  # the distinct thought survives
    # With exact-only dedup (threshold 1.0) the near-echoes are kept.
    assert len(build_examples(rows, similar_threshold=1.0)) == len(echo)


def test_agent_filter_keeps_one_character_for_a_coherent_voice() -> None:
    from sentiance.training.dataset import agent_counts

    rows = [
        {"agent": "Cass", "system": "S", "prompt": "P1", "thought": "the shadows feel heavy"},
        {"agent": "Iris", "system": "S", "prompt": "P2", "thought": "what a bright morning it is"},
        {"agent": "Cass", "system": "S", "prompt": "P3", "thought": "I brace for what comes next"},
    ]
    assert agent_counts(rows) == {"Cass": 2, "Iris": 1}
    assert len(build_examples(rows)) == 3  # blended: everyone
    assert len(build_examples(rows, agent="Cass")) == 2  # only Cass (case-insensitive)
    assert len(build_examples(rows, agent="cass")) == 2
    assert len(build_examples(rows, agent="Nobody")) == 0


def test_split_is_deterministic_and_holds_out_validation() -> None:
    examples = [{"messages": [{"role": "user", "content": str(i)}]} for i in range(100)]
    a1, b1 = split(examples, seed=0)
    a2, b2 = split(examples, seed=0)
    assert a1 == a2 and b1 == b2
    assert len(b1) == 10 and len(a1) == 90


def test_prepare_writes_train_and_val(tmp_path) -> None:
    traces = tmp_path / "traces.jsonl"
    with traces.open("w", encoding="utf-8") as f:
        for i in range(30):
            f.write(json.dumps({"system": "S", "prompt": f"P{i}",
                                "thought": f"a thought numbered {i}"}) + "\n")
    # Exact-only dedup here (thoughts differ only by a number, which the
    # near-dedup rightly treats as echoes — that behaviour is tested separately).
    stats = prepare(str(traces), str(tmp_path / "data"), similar_threshold=1.0)
    assert stats["examples"] == 30
    assert (tmp_path / "data" / "train.jsonl").exists()
    assert (tmp_path / "data" / "val.jsonl").exists()


def test_finetuned_backend_is_selected_and_falls_back_cleanly() -> None:
    from sentiance.mind.cognition import build_cognition
    from sentiance.mind.local_model import TransformersCognition

    settings = Settings(cognition_backend="finetuned", local_model_path="does/not/exist")
    assert isinstance(build_cognition(settings), TransformersCognition)

    # With no ML libs / no model present, the voice must degrade to the offline
    # one — the cognitive cycle keeps running rather than crashing.
    mind = Mind(settings=settings)
    result = mind.perceive(Stimulus(content="a curious new sound", intensity=0.6))
    assert result.moment.tick == 1
    mind.idle()  # a second tick (deliberation ran via fallback) — no error
    assert mind.tick_no == 2
