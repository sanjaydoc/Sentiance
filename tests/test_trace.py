"""Trace export — a mind's living becomes a (prompt, state) → thought dataset."""

from __future__ import annotations

import json

from sentiance.core.config import Settings
from sentiance.mind import Mind
from sentiance.mind.state import Stimulus


def _rows(path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_tracing_off_by_default_writes_nothing(tmp_path) -> None:
    path = tmp_path / "traces.jsonl"
    mind = Mind(settings=Settings())  # no trace_path
    for _ in range(3):
        mind.idle()
    assert not path.exists()


def test_each_deliberation_becomes_a_training_row(tmp_path) -> None:
    path = tmp_path / "traces.jsonl"
    mind = Mind(settings=Settings(trace_path=str(path)))
    mind.perceive(Stimulus(content="a soft chime sounds", intensity=0.6, tags=["sound"]))
    for _ in range(4):
        mind.idle()

    rows = _rows(path)
    assert len(rows) >= 3
    row = rows[0]
    # A ready supervised pair for fine-tuning the voice (Path A)...
    assert row["prompt"] and row["thought"]
    assert "My next thought is:" in row["prompt"]
    # ...plus the structured inner state of the moment (Path B).
    for key in ("emotion", "valence", "arousal", "drives", "goals"):
        assert key in row["state"]


def test_trace_carries_the_agent_name(tmp_path) -> None:
    path = tmp_path / "traces.jsonl"
    mind = Mind(settings=Settings(agent_name="Nova", trace_path=str(path)))
    mind.perceive(Stimulus(content="a bright new sight", intensity=0.6))
    mind.idle()
    rows = _rows(path)
    assert rows and all(r["agent"] == "Nova" for r in rows)


def test_a_society_writes_all_housemates_to_one_file(tmp_path) -> None:
    # Several minds sharing a trace path append through one handle, tagged by name.
    from sentiance.mind.cognition import build_cognition
    from sentiance.society import Inhabitant, Society
    from sentiance.world import World, default_home

    path = tmp_path / "society.jsonl"
    places = default_home().places
    people = []
    for name, room in [("Ada", "kitchen"), ("Bo", "kitchen")]:
        s = Settings(agent_name=name, trace_path=str(path))
        people.append(
            Inhabitant(name, Mind(settings=s, cognition=build_cognition(s)),
                       World(places=places, current=room))
        )
    society = Society(people)
    for _ in range(6):
        society.step()

    rows = _rows(path)
    names = {r["agent"] for r in rows}
    assert {"Ada", "Bo"} <= names  # both housemates' cognition captured in one dataset
