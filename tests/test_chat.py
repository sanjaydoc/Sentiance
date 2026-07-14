"""Interactive chat REPL — line parsing and a scripted end-to-end run."""

from __future__ import annotations

import builtins

from sentiance.chat import parse_line, run_chat
from sentiance.core.config import Settings
from sentiance.mind import Mind
from sentiance.mind.state import Stimulus


def test_parse_experience_extracts_tags() -> None:
    kind, arg = parse_line("a loud crash in the dark #threat #alarm")
    assert kind == "perceive"
    assert isinstance(arg, Stimulus)
    assert arg.content == "a loud crash in the dark"
    assert arg.tags == ["threat", "alarm"]


def test_parse_commands() -> None:
    assert parse_line("") == ("idle", 1)
    assert parse_line(":quit") == ("quit", None)
    assert parse_line(":help") == ("help", None)
    assert parse_line(":self") == ("self", None)
    assert parse_line(":idle 5") == ("idle", 5)
    assert parse_line(":idle") == ("idle", 3)  # default when no count


def test_run_chat_drives_the_mind(monkeypatch, capsys) -> None:
    # Feed scripted lines, then quit; the mind must perceive + reflect + report.
    lines = iter(["a friendly voice says hello #friend", ":self", ":quit"])
    monkeypatch.setattr(builtins, "input", lambda _prompt="": next(lines))

    run_chat(Mind(settings=Settings()))  # simulated backend — offline, deterministic

    out = capsys.readouterr().out
    assert "is awake" in out
    assert "friendly voice" in out
    assert "I am aware" in out  # a first-person report was printed
    assert "drives:" in out  # :self rendered the self-model
    assert "rests" in out  # clean exit
