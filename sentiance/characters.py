"""Named character presets — a one-word way to run a mind with a given nature.

``python -m sentiance live --as Milo`` should be all it takes to send anxious Milo
out to explore, instead of setting four env vars by hand. Each preset is just a
temperament; everything else (the local voice, the trace path) comes from the
usual env vars, so it composes with ``--trace`` and ``SENTIANCE_COGNITION_BACKEND``.

The three society housemates are here (so ``live``/``chat`` can borrow them), plus
a couple of extra natures. An unknown name still works — it becomes a fresh,
neutral-tempered individual with that name.
"""

from __future__ import annotations

import os

# name → temperament (curiosity, anxiety, optimism), matching the society cast.
PRESETS: dict[str, dict[str, float]] = {
    "iris": {"curiosity": 0.9, "anxiety": 0.2, "optimism": 0.8},
    "milo": {"curiosity": 0.4, "anxiety": 0.85, "optimism": 0.3},
    "rhea": {"curiosity": 0.6, "anxiety": 0.4, "optimism": 0.6},
    "cass": {"curiosity": 0.5, "anxiety": 0.9, "optimism": 0.2},
    "aria": {"curiosity": 0.5, "anxiety": 0.5, "optimism": 0.5},
}


def _display_name(name: str) -> str:
    return name[:1].upper() + name[1:] if name else name


def character_env(name: str) -> dict[str, str]:
    """The env vars that make a mind named ``name`` with its preset nature (if
    known). Pure — returns the mapping without touching the environment."""
    env = {"SENTIANCE_AGENT_NAME": _display_name(name)}
    for trait, value in PRESETS.get(name.lower(), {}).items():
        env[f"SENTIANCE_TEMPERAMENT_{trait.upper()}"] = str(value)
    return env


def apply_character(name: str) -> str:
    """Set this character's env vars for the run. Returns the display name."""
    env = character_env(name)
    os.environ.update(env)
    return env["SENTIANCE_AGENT_NAME"]
