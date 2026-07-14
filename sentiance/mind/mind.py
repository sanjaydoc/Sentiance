"""The Mind — the cognitive cycle that ties the faculties into one loop.

Each ``tick`` runs the cycle (ARCHITECTURE.md §4):

    perceive → predict/surprise → appraise → feel → attend → BROADCAST
             → remember + update self-model + reflect → learn → deliberate

The winning content is broadcast on the Global Workspace; memory, the self-model,
and metacognition are subscribers that react to it (GWT). With no external input
the mind wanders — replaying salient memories and its own last thought — so the
inner stream never stops.
"""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel

from sentiance.core.config import Settings, get_settings
from sentiance.mind.affect import AffectSystem
from sentiance.mind.attention import AttentionSystem
from sentiance.mind.cognition import Cognition, build_cognition
from sentiance.mind.drives import Drives
from sentiance.mind.embeddings import build_embedder
from sentiance.mind.goals import GoalSystem
from sentiance.mind.memory import Memory
from sentiance.mind.metacognition import Metacognition
from sentiance.mind.perception import Perceptor
from sentiance.mind.self_model import SelfModel
from sentiance.mind.state import (
    AffectState,
    Appraisal,
    Candidate,
    ConsciousMoment,
    ContentSource,
    Drive,
    IntrospectiveReport,
    Percept,
    SelfModelState,
    Stimulus,
)
from sentiance.mind.util import clamp, strip_narration
from sentiance.mind.workspace import GlobalWorkspace
from sentiance.mind.world_model import WorldModel


class TickResult(BaseModel):
    moment: ConsciousMoment
    report: IntrospectiveReport


class Mind:
    def __init__(
        self,
        settings: Settings | None = None,
        cognition: Cognition | None = None,
        workspace: GlobalWorkspace | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.workspace = workspace or GlobalWorkspace()

        self.world = WorldModel()
        self.perceptor = Perceptor()
        self.drives = Drives()
        self.affect_system = AffectSystem(
            mood_inertia=self.settings.mood_inertia,
            emotion_decay=self.settings.emotion_decay,
        )
        self.attention = AttentionSystem(self.settings.attention_temperature)
        self.memory = Memory(
            working_size=self.settings.working_memory_size,
            episodic_capacity=self.settings.episodic_capacity,
            embedder=build_embedder(self.settings),
        )
        self.self_model = SelfModel(self.settings.agent_name)
        self.metacognition = Metacognition()
        self.goals = GoalSystem()
        self.cognition = cognition or build_cognition(self.settings)

        self.affect = AffectState()
        self.tick_no = 0
        self._pending_inner: Stimulus | None = None
        self._last_moment: ConsciousMoment | None = None
        self.last_goal_events: list[tuple[str, object]] = []  # for the UI to announce

        # Per-tick scratch shared with the broadcast subscribers.
        self._appraisal = Appraisal(novelty=0.0, goal_congruence=0.0, control=1.0, relevance=0.0)
        self._dominant_drive = Drive.CURIOSITY
        self._tags: list[str] = []
        self._last_report: IntrospectiveReport | None = None

        # Wire faculties as workspace subscribers (GWT broadcast), in order.
        self.workspace.subscribe_conscious(self._on_conscious_remember)
        self.workspace.subscribe_conscious(self._on_conscious_self_model)
        self.workspace.subscribe_conscious(self._on_conscious_reflect)

    # --- public API -------------------------------------------------------

    def perceive(self, stimulus: Stimulus, *, deliberate: bool = True) -> TickResult:
        """Present an external stimulus and advance one tick.

        ``deliberate=False`` skips the built-in end-of-tick thought generation —
        used when a caller (e.g. the chat REPL) drives deliberation itself via
        ``think()`` so it can stream the thought as it forms.
        """
        return self._tick(stimulus, deliberate=deliberate)

    def idle(self, *, deliberate: bool = True) -> TickResult:
        """Advance one tick with no external input — the mind wanders."""
        return self._tick(None, deliberate=deliberate)

    def think(self, on_token: Callable[[str], None] | None = None) -> Stimulus | None:
        """Deliberate on the current conscious moment and return the next inner
        thought, streaming it through ``on_token`` if the backend supports it.

        The returned stimulus can be fed back with ``perceive(t, deliberate=False)``.
        """
        if self._last_moment is None:
            return None
        return self.cognition.deliberate(
            self._last_moment.content,
            self._last_moment.source,
            self._snapshot(),
            self.memory,
            on_token=on_token,
        )

    def live(self, stimuli: list[Stimulus], idle_after: int = 0) -> list[TickResult]:
        """Run a sequence of stimuli, then optionally ``idle_after`` free ticks."""
        results = [self.perceive(s) for s in stimuli]
        results += [self.idle() for _ in range(idle_after)]
        return results

    def state(self) -> SelfModelState:
        return self._snapshot()

    def _snapshot(self) -> SelfModelState:
        """Self-model snapshot with active goals folded in (used by cognition)."""
        s = self.self_model.snapshot()
        s.goals = self.goals.descriptions()
        return s

    def save(self, path: str) -> None:
        """Persist this mind's memory and inner state to disk (durable identity)."""
        from sentiance.mind import persistence  # noqa: PLC0415 - avoid import cycle

        persistence.save(self, path)

    def load(self, path: str) -> int:
        """Restore memory + inner state from disk; returns episodes recovered (0 if none)."""
        from sentiance.mind import persistence  # noqa: PLC0415 - avoid import cycle

        return persistence.load(self, path)

    # --- the cognitive cycle ---------------------------------------------

    def _tick(self, stimulus: Stimulus | None, *, deliberate: bool = True) -> TickResult:
        self.tick_no += 1
        incoming = stimulus or self._pending_inner or self._wander()
        self._pending_inner = None

        # 1. Perceive (novelty = prediction error against the world-model).
        percept = self.perceptor.perceive(incoming, self.world)
        self._tags = percept.tags

        # 2. Appraise against drives, then 3. feel.
        self._appraisal, self._dominant_drive = self.drives.appraise(percept)
        self.affect = self.affect_system.appraise(percept, self._appraisal, self.affect)

        # 4. Attention competition over candidate contents.
        winner, also = self.attention.select(self._candidates(percept), self.affect.arousal)
        moment = ConsciousMoment(
            tick=self.tick_no,
            content=winner.content,
            source=winner.source,
            salience=winner.salience,
            affect=self.affect,
            attention_target=winner.content,
            also_considered=also,
        )

        # 5. Broadcast → subscribers remember / update self / reflect.
        self.workspace.broadcast(moment)
        self.workspace.drain()

        # 6. Learn: fold the event into the world-model; relax drives; update goals.
        self.world.update(percept.content, percept.tags)
        self.drives.decay()
        self.last_goal_events = self.goals.update(
            moment, self._appraisal, self._dominant_drive, self.affect, self.drives.levels
        )
        self._last_moment = moment

        # 7. Deliberate: form the next inner thought (self-sustaining stream).
        # Skipped when a caller drives deliberation itself (streaming chat).
        if deliberate:
            self._pending_inner = self.cognition.deliberate(
                moment.content, moment.source, self._snapshot(), self.memory
            )

        assert self._last_report is not None
        return TickResult(moment=moment, report=self._last_report)

    # --- candidate assembly ----------------------------------------------

    def _candidates(self, percept: Percept) -> list[Candidate]:
        candidates = [
            Candidate(
                content=percept.content,
                source=ContentSource.PERCEPT,
                salience=percept.salience,
            )
        ]
        # Interoception: a strong emotion is itself a candidate for consciousness.
        if self.affect.arousal >= 0.4:
            candidates.append(
                Candidate(
                    content=f"a feeling of {self.affect.emotion.value}",
                    source=ContentSource.FEELING,
                    salience=clamp(0.3 + 0.6 * self.affect.arousal),
                )
            )
        # Associative recall cued by the current percept.
        candidates += self.memory.retrieve(percept.content, percept.tags, k=1)
        # A standing intention can intrude on consciousness ("what was I doing?").
        goal = self.goals.top()
        if goal is not None:
            candidates.append(
                Candidate(
                    content=f"my intention to {goal.description}",
                    source=ContentSource.THOUGHT,
                    salience=clamp(0.2 + 0.35 * goal.urgency),
                )
            )
        # A self-generated thought carries the THOUGHT source.
        if percept.content.startswith("I ") or "reflection" in percept.tags:
            candidates[0] = candidates[0].model_copy(update={"source": ContentSource.THOUGHT})
        return candidates

    def _wander(self) -> Stimulus:
        """No input: revisit a salient memory, or rest in bare self-awareness."""
        trace = self.memory.most_salient()
        if trace is not None:
            return Stimulus(
                content=f"(drifting) {strip_narration(trace.content)}",
                source="inner",
                intensity=0.25,
                tags=[*trace.tags, "reflection"],
            )
        return Stimulus(
            content="I notice my own awareness, quiet for now.",
            source="inner",
            intensity=0.2,
            tags=["self", "reflection"],
        )

    # --- workspace subscribers (run on broadcast, in registration order) --

    def _on_conscious_remember(self, moment: ConsciousMoment) -> None:
        self.memory.store(moment, self._tags)

    def _on_conscious_self_model(self, moment: ConsciousMoment) -> None:
        self.self_model.update(moment, self.drives.levels)

    def _on_conscious_reflect(self, moment: ConsciousMoment) -> None:
        report = self.metacognition.reflect(
            moment, self._snapshot(), self._appraisal, self._dominant_drive
        )
        self._last_report = report
        self.workspace.broadcast_report(report)
