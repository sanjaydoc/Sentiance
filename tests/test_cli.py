"""CLI conveniences — character presets and the --as / --trace flags."""

from __future__ import annotations

from sentiance.__main__ import parse_cli
from sentiance.characters import character_env


def test_parse_cli_reads_command_and_flags() -> None:
    assert parse_cli(["live", "--as", "Milo"]) == ("live", "Milo", None)
    assert parse_cli(["chat", "--as", "Cass", "--trace", "d/x.jsonl"]) == (
        "chat", "Cass", "d/x.jsonl",
    )
    assert parse_cli([]) == ("", None, None)


def test_trace_flag_defaults_to_a_path_when_bare() -> None:
    assert parse_cli(["society", "--trace"]) == ("society", None, "data/traces.jsonl")
    # order-independent, and a following flag doesn't get swallowed as the path
    assert parse_cli(["live", "--trace", "--as", "Rhea"]) == ("live", "Rhea", "data/traces.jsonl")


def test_a_preset_sets_name_and_temperament() -> None:
    env = character_env("Milo")
    assert env["SENTIANCE_AGENT_NAME"] == "Milo"
    assert env["SENTIANCE_TEMPERAMENT_ANXIETY"] == "0.85"  # Milo's anxious nature
    assert env["SENTIANCE_TEMPERAMENT_OPTIMISM"] == "0.3"


def test_an_unknown_name_is_a_fresh_neutral_individual() -> None:
    env = character_env("Bob")
    assert env == {"SENTIANCE_AGENT_NAME": "Bob"}  # named, but no preset temperament


def test_a_preset_actually_builds_that_mind() -> None:
    # Applying a preset (via the flags path) shapes the settings a Mind is built
    # from — anxious Milo really is more anxious.
    from sentiance.characters import apply_character
    from sentiance.core.config import get_settings
    from sentiance.mind import Mind

    try:
        apply_character("Milo")
        get_settings.cache_clear()
        mind = Mind()
        assert mind.settings.agent_name == "Milo"
        assert mind.temperament.anxiety == 0.85
    finally:
        import os

        for key in ("SENTIANCE_AGENT_NAME", "SENTIANCE_TEMPERAMENT_CURIOSITY",
                    "SENTIANCE_TEMPERAMENT_ANXIETY", "SENTIANCE_TEMPERAMENT_OPTIMISM"):
            os.environ.pop(key, None)
        get_settings.cache_clear()
