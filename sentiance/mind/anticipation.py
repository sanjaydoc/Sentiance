"""Felt time & anticipation — hope and dread about what is coming.

The rest of the mind lives in the present: it feels what is here now. This
faculty gives her a *future* she can feel toward. When a moment foretells
something ahead — a storm by nightfall, a friend's visit tomorrow — she holds it
as an **expectation** with a time and a charge, and the nearer it draws the more
it presses on how she feels now: a good thing coming lifts her (**hope**); a bad
thing looming weighs on her and winds her up (**dread**). Waiting itself has a
shape — anticipation swells as the hour approaches, and breaks when it arrives.

A functional correlate of prospective emotion / anticipatory affect (Loewenstein;
episodic future thinking); no claim the waiting is felt.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sentiance.mind.state import Emotion
from sentiance.mind.util import clamp, tokenize

# Cues that a moment points *forward* in time.
_FUTURE_WORDS = frozenset(
    {
        "will", "soon", "later", "tomorrow", "upcoming", "approaching", "coming",
        "awaits", "ahead", "nightfall", "tonight", "impending", "looming", "next",
    }
)
_FUTURE_PHRASES = ("going to", "about to", "have to", "due to")

_GOOD = frozenset({"reward", "praise", "warmth", "friend", "play", "beauty", "success",
                   "reunion", "gift", "feast", "visit"})
_BAD = frozenset({"threat", "danger", "pain", "loss", "storm", "exam", "trial",
                  "reckoning", "alarm", "attack"})


def _valence_of(tokens: set[str], tags: set[str]) -> float:
    good = len((tokens | tags) & _GOOD)
    bad = len((tokens | tags) & _BAD)
    if good == bad:
        return 0.0
    return 0.6 if good > bad else -0.6


def points_forward(text: str) -> bool:
    lowered = text.lower()
    words = set(lowered.split())
    return bool(words & _FUTURE_WORDS) or any(p in lowered for p in _FUTURE_PHRASES)


@dataclass
class Expectation:
    description: str
    valence: float  # good (hoped-for) or bad (dreaded)
    created: int
    due: int
    certainty: float = 0.8

    def proximity(self, now: int) -> float:
        """0 when just formed, →1 as its hour arrives (how near it feels)."""
        span = max(1, self.due - self.created)
        return clamp(1.0 - (self.due - now) / span)


@dataclass
class Anticipation:
    horizon: int = 8  # how many ticks ahead a foretold thing is placed
    strength: float = 0.35  # how hard the future presses on the present
    pending: list[Expectation] = field(default_factory=list)

    def note(self, content: str, tags: list[str], now: int) -> Expectation | None:
        """If this moment foretells something charged, hold it as an expectation."""
        if not points_forward(content):
            return None
        tokens = set(tokenize(content))
        valence = _valence_of(tokens, {t.lower() for t in tags})
        if valence == 0.0:
            return None
        key = " ".join(t for t in tokenize(content) if t not in _FUTURE_WORDS)[:60]
        if any(e.description == key for e in self.pending):
            return None
        exp = Expectation(description=key, valence=valence, created=now, due=now + self.horizon)
        self.pending.append(exp)
        return exp

    def due(self, now: int) -> list[Expectation]:
        """Expectations whose time has come (removed from pending)."""
        arrived = [e for e in self.pending if now >= e.due]
        self.pending = [e for e in self.pending if now < e.due]
        return arrived

    def feeling(self, now: int) -> tuple[float, float, Emotion] | None:
        """The anticipatory pull on the present from the most pressing expectation:
        (valence nudge, arousal nudge, hope/dread), or None if nothing looms."""
        if not self.pending:
            return None
        exp = max(self.pending, key=lambda e: e.certainty * e.proximity(now) * abs(e.valence))
        weight = exp.certainty * exp.proximity(now)
        if weight < 0.05:
            return None
        pull = self.strength * weight * exp.valence
        if exp.valence >= 0:
            return (pull, 0.15 * weight, Emotion.HOPE)
        return (pull, 0.3 * weight, Emotion.DREAD)  # dread also winds her up

    def looming(self, now: int) -> Expectation | None:
        return max(
            self.pending,
            key=lambda e: e.certainty * e.proximity(now) * abs(e.valence),
            default=None,
        )

    def dump(self) -> dict:
        return {
            "pending": [
                {"description": e.description, "valence": e.valence, "created": e.created,
                 "due": e.due, "certainty": e.certainty}
                for e in self.pending
            ]
        }

    def load(self, data: dict) -> None:
        self.pending = [
            Expectation(
                description=e["description"], valence=float(e["valence"]),
                created=int(e["created"]), due=int(e["due"]), certainty=float(e["certainty"]),
            )
            for e in data.get("pending", [])
        ]
