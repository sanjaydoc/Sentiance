"""Empathy — catching what another seems to feel (emotional contagion).

Theory-of-mind, so far, tracked what she feels *about* a person. Empathy is the
other half: reading what the person themselves seems to feel, and letting it bleed
into her own affect. A friend's laughter lifts her; a friend's tears pull her
down. The contagion is stronger the closer the bond — she is moved most by those
she loves — but even a stranger's plain distress reaches her a little.

A functional correlate of emotional contagion / affective empathy (Hatfield;
Preston & de Waal); no claim she feels the other's feeling as her own.
"""

from __future__ import annotations

from sentiance.mind.util import clamp

# Words that betray how another is feeling → the (valence, arousal) they suggest.
_EXPRESSIONS: list[tuple[frozenset[str], float, float]] = [
    # high-arousal joy
    (frozenset({"laughs", "laughing", "laughter", "beaming", "delighted", "thrilled",
                "excited", "overjoyed", "gleeful", "cheering"}), 0.75, 0.65),
    # warm, low-arousal contentment
    (frozenset({"smiles", "smiling", "calm", "content", "contented", "peaceful",
                "serene", "relaxed", "soothed", "gentle"}), 0.5, 0.3),
    # high-arousal distress
    (frozenset({"crying", "sobbing", "weeping", "screaming", "wailing", "panicked",
                "terrified", "frightened", "scared", "trembling", "furious", "raging",
                "shaking"}), -0.75, 0.7),
    # low-arousal sorrow
    (frozenset({"sad", "saddened", "grieving", "grief", "sorrow", "sorrowful", "down",
                "weary", "lonely", "gloomy", "miserable", "despondent", "hurt",
                "heartbroken", "tearful"}), -0.6, 0.3),
]


class Empathy:
    """Infer a present person's feeling from how they're described, and how much
    of it she takes on."""

    def read(self, text: str) -> tuple[float, float] | None:
        """The (valence, arousal) another person seems to be feeling, or None if
        the moment says nothing about how they feel."""
        words = {w.strip(".,!?;:'\"").lower() for w in text.split()}
        for cues, valence, arousal in _EXPRESSIONS:
            if words & cues:
                return (valence, arousal)
        return None

    def contagion(self, closeness: float, base: float = 0.25) -> float:
        """The fraction of another's feeling she catches — a little from anyone,
        far more from someone she is close to."""
        return clamp(base + 0.5 * closeness)
