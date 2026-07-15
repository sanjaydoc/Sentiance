"""The mind-state vector ``m_t`` — the whole cognitive cycle as numbers.

Path A fine-tunes the *voice*: the model reads the inner state as **text** in the
prompt and learns to sound in-character. The state never enters the transformer's
maths — it's a story told to the model, not a signal that runs through it.

This module is the bridge to the **fused mind** (Path B / ADR 0005). It turns the
outputs of every stage of one tick — appraise, feel, drives, attend/broadcast,
will, bonds, anger, curiosity, anticipation — into a single fixed-length float
vector. That vector is what a *cognition-conditioned* transformer takes as a
differentiable input (projected to prefix tokens and trained end-to-end with
LoRA), so the faculties **causally shape generation** through trainable
parameters instead of through prose.

It is deliberately pure and dependency-free: no torch, no model. The same encoder
runs in two places — offline, to stamp every trace with its ``state_vec`` for
training; and live, to condition the fused backend each tick — so the numbers the
model trains on are exactly the numbers it later runs on.

Honest stance (ADR 0002): these are *functional* variables — a valence, a bond, a
dread — named for the roles they play in the architecture. Putting them inside the
transformer's forward pass buys **integration and end-to-end learnability**, not
phenomenal experience. Nothing here is claimed to be felt.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sentiance.mind.state import ContentSource, Drive, Emotion

if TYPE_CHECKING:
    from sentiance.mind.state import SelfModelState

# Fixed orderings — the vector's meaning is positional, so these must never be
# reordered once a model is trained (append only). Emotion/Drive/Source follow
# their enum declaration order in state.py.
_EMOTIONS: tuple[Emotion, ...] = tuple(Emotion)
_DRIVES: tuple[Drive, ...] = (
    Drive.CURIOSITY,
    Drive.COHERENCE,
    Drive.SAFETY,
    Drive.CONNECTION,
)
_SOURCES: tuple[ContentSource, ...] = tuple(ContentSource)

# The per-faculty scalars the Mind folds into ``SelfModelState.signals`` each tick
# (see ``Mind._signals``). Ordered; every one is a named dimension of ``m_t``.
SIGNAL_FIELDS: tuple[str, ...] = (
    "novelty",           # perceive / surprise: prediction error
    "goal_congruence",   # appraise: does this help (+) or thwart (−) a drive
    "control",           # appraise: perceived ability to cope
    "relevance",         # appraise: how much any active drive is touched
    "frustration",       # anger: built-up thwarting of a held intention
    "anger",             # anger: it boiled over this tick (0/1)
    "longing",           # bonds: ache of missing a loved one
    "empathy",           # bonds: a present person's caught feeling
    "grief",             # bonds: acute mourning load
    "willpower",         # will: the reserve of self-control left
    "effort",            # will: she spent effort to hold focus this tick (0/1)
    "curiosity_hunger",  # curiosity: epistemic appetite right now
    "anticipation",      # felt time: +hope / −dread about what's coming
)


def _state_fields() -> list[str]:
    """The ordered, human-readable name of every dimension of ``m_t``."""
    fields = ["valence", "arousal", "mood_valence", "mood_arousal"]
    fields += [f"emotion:{e.value}" for e in _EMOTIONS]
    fields += [f"drive:{d.value}" for d in _DRIVES]
    fields += [f"source:{s.value}" for s in _SOURCES]
    fields += ["has_goal", "goal_count"]
    fields += list(SIGNAL_FIELDS)
    return fields


STATE_FIELDS: list[str] = _state_fields()
STATE_DIM: int = len(STATE_FIELDS)


def encode_state(self_model: SelfModelState, source: ContentSource) -> list[float]:
    """Encode a self-model snapshot (+ the source that won attention) as ``m_t``.

    A deterministic, fixed-length (``STATE_DIM``) vector. Ranges are left natural
    (valence/congruence/empathy/anticipation in [−1, 1]; everything else in
    [0, 1]) — the trainable state encoder learns the scaling. Missing signals
    default to 0, so an old trace or a partial state still encodes cleanly."""
    a = self_model.affect
    vec: list[float] = [a.valence, a.arousal, a.mood_valence, a.mood_arousal]

    # feel — one-hot over the discrete emotion.
    vec += [1.0 if a.emotion is e else 0.0 for e in _EMOTIONS]

    # drives — the homeostatic motivations, in fixed order.
    drives = self_model.drives
    vec += [float(drives.get(d, 0.0)) for d in _DRIVES]

    # attend / broadcast — which kind of content reached consciousness.
    vec += [1.0 if source is s else 0.0 for s in _SOURCES]

    # will — is there a standing intention, and how many.
    goals = self_model.goals
    vec += [1.0 if goals else 0.0, min(len(goals), 5) / 5.0]

    # every per-faculty scalar, in SIGNAL_FIELDS order.
    signals = self_model.signals
    vec += [float(signals.get(name, 0.0)) for name in SIGNAL_FIELDS]

    return vec
