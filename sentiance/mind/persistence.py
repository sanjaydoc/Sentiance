"""Durable identity — save and restore a mind's memory and inner state to disk.

A mind is otherwise reborn each run. Persisting its episodic/semantic memory,
self-model narrative, drives, mood, world-model, and tick count lets the same
individual (e.g. "Aria") continue across sessions — remembering what happened
before rather than waking blank each time.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from sentiance.mind.state import AffectState

if TYPE_CHECKING:
    from sentiance.mind.mind import Mind

SCHEMA_VERSION = 1


def snapshot(mind: Mind) -> dict:
    """Serialize the mind's durable state to a plain dict."""
    return {
        "version": SCHEMA_VERSION,
        "name": mind.self_model.name,
        "tick": mind.tick_no,
        "affect": mind.affect.model_dump(),
        "drives": mind.drives.dump(),
        "memory": mind.memory.dump(),
        "world": mind.world.dump(),
        "self_model": mind.self_model.dump(),
        "goals": mind.goals.dump(),
        "relationships": mind.relationships.dump(),
        "needs": mind.needs.dump(),
        "curiosity": mind.curiosity.dump(),
        "temperament": mind.temperament.dump(),
        "frustration": mind.frustration.dump(),
        "grief": mind.grief.dump(),
        "volition": mind.volition.dump(),
        "anticipation": mind.anticipation.dump(),
    }


def restore(mind: Mind, data: dict) -> None:
    """Load durable state (from :func:`snapshot`) back into a mind in place."""
    mind.tick_no = int(data.get("tick", 0))
    mind.affect = AffectState(**data["affect"]) if "affect" in data else mind.affect
    mind.drives.load(data.get("drives", {}))
    mind.memory.load(data.get("memory", {}))
    mind.world.load(data.get("world", {}))
    mind.self_model.load(data.get("self_model", {}))
    mind.goals.load(data.get("goals", {}))
    mind.relationships.load(data.get("relationships", {}))
    mind.needs.load(data.get("needs", {}))
    mind.curiosity.load(data.get("curiosity", {}))
    mind.temperament.load(data.get("temperament", {}))
    mind.frustration.load(data.get("frustration", {}))
    mind.grief.load(data.get("grief", {}))
    mind.volition.load(data.get("volition", {}))
    mind.anticipation.load(data.get("anticipation", {}))


def save(mind: Mind, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(snapshot(mind), indent=2), encoding="utf-8")


def load(mind: Mind, path: str | Path) -> int:
    """Restore a mind from ``path``. Returns how many episodic memories were
    recovered (0 if the file is missing, unreadable, or a schema mismatch)."""
    p = Path(path)
    if not p.exists():
        return 0
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if data.get("version") != SCHEMA_VERSION:
            return 0
        restore(mind, data)
    except (OSError, ValueError, KeyError):
        return 0
    return len(mind.memory.episodic)
