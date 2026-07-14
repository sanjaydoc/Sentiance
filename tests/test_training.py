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
    stats = prepare(str(traces), str(tmp_path / "data"))
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
