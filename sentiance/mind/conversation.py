"""Conversational memory — holding on to what others have said to her.

Bonding through the world already works, but a mind that only ever perceives the
*latest* line drifts: attention wanders to a memory or a feeling and the reply
loses the thread, so exchanges circle. This faculty keeps a short, per-person
record of what each person has recently **said** to her, so — whatever wins the
spotlight this moment — the live conversation stays in view and she can pick up
the thread ("you mentioned the cherry blossoms…") instead of starting over.

A functional correlate of dialogue/common-ground memory (Clark's grounding); no
claim the remembering is experienced.
"""

from __future__ import annotations

import re
from collections import deque

# "@Iris, beaming, says: <what she said>" / "@Milo says: <line>"
SAYS_RE = re.compile(r"@(\w+)[^:]*\bsays:\s*(.+)", re.IGNORECASE)


class Conversation:
    def __init__(self, span: int = 6) -> None:
        self.span = span
        self.heard_lines: dict[str, deque[str]] = {}

    def heard(self, name: str, text: str) -> None:
        """Record that ``name`` said ``text`` to her."""
        text = text.strip()
        if not name or not text:
            return
        self.heard_lines.setdefault(name, deque(maxlen=self.span)).append(text)

    def last(self, name: str) -> str | None:
        """The most recent thing ``name`` said to her, if any."""
        lines = self.heard_lines.get(name)
        return lines[-1] if lines else None

    def recent(self, name: str, n: int = 3) -> list[str]:
        lines = self.heard_lines.get(name)
        return list(lines)[-n:] if lines else []

    def dump(self) -> dict:
        return {"heard": {name: list(lines) for name, lines in self.heard_lines.items()}}

    def load(self, data: dict) -> None:
        self.heard_lines = {
            name: deque(lines, maxlen=self.span)
            for name, lines in data.get("heard", {}).items()
        }
