"""The tiny .env loader — feeds HF_TOKEN and SENTIANCE_* into the environment."""

from __future__ import annotations

from sentiance.core.dotenv import load_dotenv


def test_loads_pairs_without_overriding_real_env(tmp_path, monkeypatch) -> None:
    import os

    env = tmp_path / ".env"
    env.write_text(
        "# a comment\n"
        "SENTIANCE_DOTENV_TOKEN=hf_abc123\n"
        'export SENTIANCE_DOTENV_NAME="Nova"\n'
        "SENTIANCE_DOTENV_BLANK=\n"
        "\n"
        "SENTIANCE_DOTENV_KEPT=fromfile\n",
        encoding="utf-8",
    )
    # Use throwaway keys + monkeypatch so nothing leaks into other tests.
    for key in ("SENTIANCE_DOTENV_TOKEN", "SENTIANCE_DOTENV_NAME", "SENTIANCE_DOTENV_BLANK"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("SENTIANCE_DOTENV_KEPT", "real")  # a real env var must win

    # load_dotenv writes to os.environ directly; record what it adds so we can undo.
    before = set(os.environ)
    try:
        n = load_dotenv(env)
        assert os.environ["SENTIANCE_DOTENV_TOKEN"] == "hf_abc123"
        assert os.environ["SENTIANCE_DOTENV_NAME"] == "Nova"  # quotes stripped, export dropped
        assert os.environ["SENTIANCE_DOTENV_BLANK"] == ""
        assert os.environ["SENTIANCE_DOTENV_KEPT"] == "real"  # not overridden
        assert n == 3
    finally:
        for key in set(os.environ) - before:
            os.environ.pop(key, None)


def test_missing_file_is_a_silent_noop() -> None:
    assert load_dotenv("/no/such/path/.env") == 0
