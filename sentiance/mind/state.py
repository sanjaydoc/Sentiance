"""The mind's data contracts: percepts, appraisals, affect, conscious moments.

These are the vocabulary the faculties speak in. Everything the architecture
does is a transformation between these types along the cognitive cycle
(ARCHITECTURE.md §4).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

# --- Global-workspace topics (broadcast channels) -------------------------

TOPIC_CONSCIOUS = "workspace.conscious"  # the current contents of consciousness
TOPIC_INTROSPECTION = "workspace.introspection"  # metacognitive self-reports


# --- Enums ----------------------------------------------------------------


class Emotion(StrEnum):
    """Discrete emotions, derived from the affect circumplex + appraisal."""

    JOY = "joy"
    CONTENTMENT = "contentment"
    CURIOSITY = "curiosity"
    SURPRISE = "surprise"
    FEAR = "fear"
    ANGER = "anger"
    SADNESS = "sadness"
    CONFUSION = "confusion"
    NEUTRAL = "neutral"


class Drive(StrEnum):
    """Intrinsic, homeostatic motivations — what the mind 'cares about'."""

    CURIOSITY = "curiosity"  # seek novelty / understanding
    COHERENCE = "coherence"  # minimize surprise / maintain a consistent world-model
    SAFETY = "safety"  # avoid threat
    CONNECTION = "connection"  # social relatedness


class ContentSource(StrEnum):
    """Where a candidate for consciousness came from."""

    PERCEPT = "percept"  # bottom-up, from the world
    FEELING = "feeling"  # interoception — an emotion strong enough to notice
    MEMORY = "memory"  # a recalled episode
    THOUGHT = "thought"  # top-down, self-generated (mind-wandering / deliberation)


# --- Perception -----------------------------------------------------------


class Stimulus(BaseModel):
    """Something presented to the mind (external event or internal prompt)."""

    content: str
    source: str = "world"
    intensity: float = Field(0.5, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    # Optional hint of intrinsic pleasantness, if the environment provides it.
    valence_hint: float | None = Field(None, ge=-1.0, le=1.0)


class Percept(BaseModel):
    """An encoded stimulus with computed novelty and bottom-up salience."""

    content: str
    tags: list[str]
    intensity: float
    novelty: float = Field(ge=0.0, le=1.0)  # prediction error from the world-model
    salience: float = Field(ge=0.0, le=1.0)
    valence_hint: float | None = None
    internal: bool = False  # self-generated (an inner thought) vs. from the world


# --- Appraisal & affect ---------------------------------------------------


class Appraisal(BaseModel):
    """How an event stands relative to the mind's drives (appraisal theory)."""

    novelty: float = Field(ge=0.0, le=1.0)
    goal_congruence: float = Field(ge=-1.0, le=1.0)  # helps (+) or thwarts (−) drives
    control: float = Field(ge=0.0, le=1.0)  # perceived ability to cope
    relevance: float = Field(ge=0.0, le=1.0)  # how much any active drive is touched


class AffectState(BaseModel):
    """The mind's current feeling: dimensional (valence/arousal) + discrete."""

    valence: float = Field(0.0, ge=-1.0, le=1.0)
    arousal: float = Field(0.0, ge=0.0, le=1.0)
    emotion: Emotion = Emotion.NEUTRAL
    # Mood is the slow-moving background affect (EMA of valence/arousal).
    mood_valence: float = Field(0.0, ge=-1.0, le=1.0)
    mood_arousal: float = Field(0.0, ge=0.0, le=1.0)


# --- Consciousness --------------------------------------------------------


class Candidate(BaseModel):
    """A contender for the spotlight of consciousness."""

    content: str
    source: ContentSource
    salience: float = Field(ge=0.0, le=1.0)


class ConsciousMoment(BaseModel):
    """The single content that won the attention competition this tick — the
    thing the mind is conscious *of* right now, broadcast to all faculties."""

    tick: int
    content: str
    source: ContentSource
    salience: float
    affect: AffectState
    attention_target: str
    # The runners-up — the coalition that lost the competition this tick.
    also_considered: list[Candidate] = Field(default_factory=list)


class IntrospectiveReport(BaseModel):
    """A first-person, higher-order report *about* the current conscious state."""

    tick: int
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    emotion: Emotion


class MemoryTrace(BaseModel):
    """An episodic memory: a conscious moment laid down with its affective charge."""

    tick: int
    content: str
    tags: list[str]
    emotion: Emotion
    valence: float
    salience: float


class SelfModelState(BaseModel):
    """The mind's model of itself — the substrate of self-report (AST)."""

    name: str
    tick: int
    current_focus: str
    affect: AffectState
    drives: dict[Drive, float]
    narrative: str  # a running, compressed autobiography
