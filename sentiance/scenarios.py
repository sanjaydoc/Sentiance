"""Preset chat scenarios — curated scripts that walk a mind through varied
situations hands-free, so collecting broad training data is one command.

Each scenario is just the lines you'd otherwise type at the ``you>`` prompt
(experiences with ``#tags``, ``@people``, and ``:commands``), ordered to touch the
whole emotional range: warmth, fear, curiosity, a blocked goal turning to anger, a
bond that is built and then lost, empathy, hope and dread of the future, sadness,
and sleep/dreams. Run with ``python -m sentiance chat --preset`` (add ``--as
<Name>`` for a given nature, ``--trace`` to log it for training).
"""

from __future__ import annotations

# The default "varied" scenario — a full sweep across the faculties.
_VARIED: list[str] = [
    # — warmth, joy, connection —
    "@Sam waves warmly across the room #friend",
    "@Sam is laughing with delight #friend",
    "a warm cup of tea in the morning light #reward #warmth",
    "soft music drifts through the house #beauty",
    # — fear, threat —
    "a sudden loud crash in the dark #threat #alarm",
    "footsteps behind me on an empty street #threat",
    "the smell of smoke somewhere in the house #threat #alarm",
    # — curiosity, novelty, the "aha" (repeat so it becomes familiar) —
    "a strange glowing symbol on the wall #beauty",
    "a door I have never noticed before",
    "a strange glowing symbol on the wall",
    # — an intention, then blocked until it turns to anger —
    "I want to reach the far room",
    "I want to reach the far room",
    "the far door is locked and won't budge #loss",
    "the far door still won't budge #loss",
    "the far door still won't budge #loss",
    # — a bond built, then lost (attachment → grief) —
    "@Mara holds my hand warmly #friend #warmth",
    "@Mara holds my hand warmly #friend #warmth",
    "@Mara holds my hand warmly #friend #warmth",
    ":people",
    "@Mara is gone forever",
    ":idle 5",
    # — empathy: catching another's feeling —
    "@Kai is crying, heartbroken #friend",
    "@Kai is laughing with joy #friend",
    "@Noor looks frightened and trembling",
    # — hope and dread of the future —
    "a warm reunion with friends is coming tomorrow #reward #friend",
    "a fierce storm will come tonight #threat",
    "an important day is approaching soon",
    ":idle 4",
    # — sadness, solitude, reflection —
    "an empty room where laughter used to be #loss",
    "grey rain against the window all afternoon",
    ":idle 5",
    ":sleep",
    # — close out: self-report, a last dream, save & leave —
    ":self",
    ":sleep",
    ":quit",
]

SCENARIOS: dict[str, list[str]] = {
    "varied": _VARIED,
}


def scenario(name: str | None = None) -> list[str]:
    """The lines of a named scenario (defaults to 'varied'); unknown → 'varied'."""
    return list(SCENARIOS.get((name or "varied").lower(), _VARIED))
