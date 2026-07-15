"""CLI conveniences — character presets and the --as / --trace flags."""

from __future__ import annotations

from sentiance.__main__ import parse_cli
from sentiance.characters import character_env


def test_parse_cli_reads_command_and_flags() -> None:
    assert parse_cli(["live", "--as", "Milo"]) == ("live", "Milo", None, None)
    assert parse_cli(["chat", "--as", "Cass", "--trace", "d/x.jsonl"]) == (
        "chat", "Cass", "d/x.jsonl", None,
    )
    assert parse_cli([]) == ("", None, None, None)


def test_trace_and_preset_flags_default_when_bare() -> None:
    assert parse_cli(["society", "--trace"]) == ("society", None, "data/traces.jsonl", None)
    assert parse_cli(["chat", "--preset"]) == ("chat", None, None, "varied")
    # order-independent; a following flag isn't swallowed as a value
    assert parse_cli(["chat", "--as", "Cass", "--preset", "--trace"]) == (
        "chat", "Cass", "data/traces.jsonl", "varied",
    )


def test_scenario_is_a_playable_script() -> None:
    from sentiance.scenarios import scenario

    lines = scenario("varied")
    assert len(lines) > 20
    assert lines[-1] == ":quit"  # ends by saving and leaving
    assert any(line.startswith("@") for line in lines)  # has people
    assert scenario("nope") == scenario()  # unknown → default


def test_scripted_chat_plays_the_scenario_hands_free(tmp_path) -> None:
    import io
    from contextlib import redirect_stdout

    from sentiance.chat import run_chat
    from sentiance.core.config import Settings
    from sentiance.mind import Mind
    from sentiance.scenarios import scenario

    mind = Mind(settings=Settings())
    path = tmp_path / "aria.json"
    with redirect_stdout(io.StringIO()):
        run_chat(mind=mind, persist_path=str(path), script=scenario("varied"))

    assert mind.tick_no > 20  # it ran the whole scenario
    assert path.exists()  # saved on :quit
    assert mind.relationships.known("Mara") is not None  # she met the people in it


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
