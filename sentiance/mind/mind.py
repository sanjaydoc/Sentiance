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
from sentiance.mind.anticipation import Anticipation
from sentiance.mind.attention import AttentionSystem
from sentiance.mind.cognition import Cognition, build_cognition
from sentiance.mind.conscience import Conscience, SelfJudgment
from sentiance.mind.curiosity import Curiosity
from sentiance.mind.drives import Drives
from sentiance.mind.embeddings import build_embedder
from sentiance.mind.empathy import Empathy
from sentiance.mind.frustration import Frustration
from sentiance.mind.goals import GoalSystem
from sentiance.mind.grief import Grief, signals_loss
from sentiance.mind.imagination import Imagination, Prospect
from sentiance.mind.memory import Memory
from sentiance.mind.metacognition import Metacognition
from sentiance.mind.perception import Perceptor
from sentiance.mind.relationships import RelationshipSystem, extract_people
from sentiance.mind.self_model import SelfModel
from sentiance.mind.state import (
    AffectState,
    Appraisal,
    Candidate,
    ConsciousMoment,
    ContentSource,
    Drive,
    Emotion,
    Goal,
    IntrospectiveReport,
    Percept,
    SelfModelState,
    Stimulus,
)
from sentiance.mind.temperament import Needs, Temperament
from sentiance.mind.util import clamp, strip_narration, tokenize
from sentiance.mind.volition import Volition
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
        self.relationships = RelationshipSystem()
        self.temperament = Temperament(
            curiosity=self.settings.temperament_curiosity,
            anxiety=self.settings.temperament_anxiety,
            optimism=self.settings.temperament_optimism,
            plasticity=self.settings.temperament_plasticity,
        )
        self.needs = Needs()
        self.curiosity = Curiosity()
        self.conscience = Conscience()
        self.frustration = Frustration()
        self.empathy = Empathy()
        self.grief = Grief()
        self.volition = Volition()
        self.anticipation = Anticipation()
        self.imagination = Imagination(
            self.perceptor, self.drives, self.affect_system, self.temperament
        )
        self.cognition = cognition or build_cognition(self.settings)

        self.affect = AffectState()
        self.tick_no = 0
        self._pending_inner: Stimulus | None = None
        self._last_moment: ConsciousMoment | None = None
        self.last_goal_events: list[tuple[str, object]] = []  # for the UI to announce
        self.last_curiosity: tuple[str, float] | None = None  # an "aha", for the UI
        self.last_self_judgment: SelfJudgment | None = None  # pride/disappointment
        self.last_anger: bool = False  # frustration boiled over this tick, for the UI
        self.longing: tuple[str, float] | None = None  # who she misses, for the UI
        self.last_empathy: tuple[str, float] | None = None  # whose feeling she caught
        self.grieving: bool = False  # mourning a loss, for the UI
        self.last_dream: object | None = None  # the last dream she had, for the UI
        self.last_effort: bool = False  # she held focus by will this tick, for the UI
        self.last_anticipation: tuple[str, Emotion] | None = None  # what she awaits, for the UI

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

    def sleep(self) -> list[str]:
        """Reflect and consolidate: distil recurring experience into durable
        beliefs, *dream* (recombine memory into something new), and rest (the acute
        feeling calms toward the background mood). Returns the newly-formed beliefs."""
        from sentiance.mind.consolidation import consolidate  # noqa: PLC0415 - cycle
        from sentiance.mind.dreaming import dream  # noqa: PLC0415 - avoid import cycle

        added = self.self_model.add_beliefs(consolidate(self.memory))

        # Dream: weave charged memory fragments into something that never happened.
        # She wakes remembering it — the recombination forges new associations, and
        # a vivid dream leaves a fresh intention to make sense of it.
        self.last_dream = dream(self.memory, self.tick_no)
        if self.last_dream is not None:
            d = self.last_dream
            self.tick_no += 1
            dream_moment = ConsciousMoment(
                tick=self.tick_no,
                content=d.narrative,
                source=ContentSource.THOUGHT,
                salience=0.5,
                affect=AffectState(
                    valence=d.tone,
                    arousal=0.3,
                    emotion=d.emotion,
                    mood_valence=self.affect.mood_valence,
                    mood_arousal=self.affect.mood_arousal,
                ),
                attention_target=d.narrative,
            )
            self.memory.store(dream_moment, ["dream"])  # remembered + newly associated
            if abs(d.tone) >= 0.4 and d.fragments:
                self.goals.goals.append(
                    Goal(
                        description=f"make sense of my dream of {d.fragments[0]}",
                        drive=Drive.CURIOSITY,
                        created_tick=self.tick_no,
                        updated_tick=self.tick_no,
                        urgency=0.5,
                    )
                )

        self.needs.rest_now()  # a night's rest
        self.volition.restore()  # willpower is renewed by rest
        mv = self.affect.mood_valence
        self.affect = AffectState(
            valence=round(mv * 0.4, 3),
            arousal=0.2,
            emotion=Emotion.CONTENTMENT if mv >= 0 else Emotion.NEUTRAL,
            mood_valence=mv,
            mood_arousal=round(self.affect.mood_arousal * 0.6, 3),
        )
        return added

    def foresee(self, options: list[tuple[str, Stimulus]]) -> list[Prospect]:
        """Imagine each ``(label, hypothetical)`` option and rank them by how
        appealing the anticipated moment feels — a forward model that mutates
        nothing. The mind can then choose the future it expects to like best."""
        return self.imagination.imagine(
            options, self.world, self.affect, self.curiosity.appeal_bonus(self.drives.levels)
        )

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

        # 1b. Known people color the appraisal before anything happens — a warm
        # friend feels good on sight; a hurtful person puts her on edge. Merely
        # *thinking* of someone still colours the feeling, but only an external
        # encounter counts as them actually being *present* (§3b) — otherwise she
        # could never miss anyone, since remembering them would summon them.
        people = extract_people(percept.content)
        present = [] if percept.internal else people
        prior = self.relationships.prior(people)
        if prior is not None and percept.valence_hint is None:
            percept = percept.model_copy(update={"valence_hint": round(prior, 3)})

        # 2. Appraise against drives, shaped by temperament + the pressure of any
        #    unmet needs, then 3. feel.
        self._appraisal, self._dominant_drive = self.drives.appraise(percept)
        self._appraisal = self.temperament.shape(self._appraisal)
        self._appraisal = self._appraisal.model_copy(
            update={
                "goal_congruence": clamp(
                    self._appraisal.goal_congruence + 0.5 * self.needs.pressure(), -1.0, 1.0
                )
            }
        )
        self.affect = self.affect_system.appraise(percept, self._appraisal, self.affect)

        # 3a. Intrinsic curiosity: if this moment resolves something she'd been
        #     wondering about (once surprising, now familiar), understanding it
        #     lifts her feeling and feeds the curiosity drive — the quiet "aha".
        aha = self.curiosity.observe(percept.content, percept.novelty)
        self.last_curiosity = None
        if aha > 0.0:
            self.affect = self.affect.model_copy(
                update={"valence": clamp(self.affect.valence + aha, -1.0, 1.0)}
            )
            self.drives.levels[Drive.CURIOSITY] = clamp(
                self.drives.levels[Drive.CURIOSITY] + 0.5 * aha
            )
            self.last_curiosity = (percept.content, aha)

        # 3b. Fold how this encounter felt into each person's model, and let the
        #     moment deplete/replenish the homeostatic needs.
        if present:
            self.relationships.record(present, self.affect.valence, self.tick_no)

        # 3b-i. Attachment: a loved one present warms her and fills her need for
        #       connection; one long absent is *missed* — a longing that aches a
        #       little and leaves her lonelier the deeper the bond.
        bond = self.relationships.bond(present)
        if bond > 0.0:
            self.affect = self.affect.model_copy(
                update={"valence": clamp(self.affect.valence + 0.2 * bond, -1.0, 1.0)}
            )
            self.needs.connection = clamp(self.needs.connection + 0.15 * bond)
        self.longing = self.relationships.missing(self.tick_no, set(present))
        if self.longing is not None:
            ache = self.longing[1]
            self.affect = self.affect.model_copy(
                update={"valence": clamp(self.affect.valence - 0.15 * ache, -1.0, 1.0)}
            )
            self.needs.connection = clamp(self.needs.connection - 0.1 * ache)

        # 3b-ii. Empathy: if a present person's feeling shows, she catches it —
        #        more from someone she's close to, a little from anyone.
        self.last_empathy = None
        if present:
            felt = self.empathy.read(percept.content)
            if felt is not None:
                other_v, other_a = felt
                w = self.empathy.contagion(self.relationships.bond(present))
                self.affect = self.affect.model_copy(
                    update={
                        "valence": clamp(
                            (1 - w) * self.affect.valence + w * other_v, -1.0, 1.0
                        ),
                        "arousal": clamp((1 - w) * self.affect.arousal + w * other_a),
                    }
                )
                self.last_empathy = (present[0], round(other_v, 3))

        # 3b-iii. Loss & grief: if a loved one is named as gone, the bond turns to
        #         mourning — a sadness deep as the attachment and slow to fade,
        #         pulling down the passing feeling and the background mood alike.
        if present and signals_loss(percept.content):
            for name in present:
                rel = self.relationships.known(name)
                if rel is None or rel.lost:
                    continue
                # How much there is to mourn: the deep bond, or — for someone she
                # hasn't known long but is warmly fond of — that fondness stands in.
                depth = max(rel.attachment, 0.6 * max(0.0, rel.affection))
                if depth >= 0.15:
                    rel.lost = True
                    self.grief.bereave(name, depth)
        grief_pull = self.grief.step()
        self.grieving = grief_pull < -0.05
        if grief_pull < 0.0:
            self.affect = self.affect.model_copy(
                update={
                    "valence": clamp(self.affect.valence + grief_pull, -1.0, 1.0),
                    "mood_valence": clamp(self.affect.mood_valence + 0.3 * grief_pull, -1.0, 1.0),
                    "emotion": Emotion.GRIEF if grief_pull < -0.3 else self.affect.emotion,
                }
            )

        # 3g. Felt time: note anything foretold, let hope/dread about what's coming
        #     colour the present (swelling as it nears), and let arrivals land.
        if not percept.internal:
            self.anticipation.note(percept.content, percept.tags, self.tick_no)
        for arrived in self.anticipation.due(self.tick_no):
            self.affect = self.affect.model_copy(  # the awaited thing is here now
                update={"valence": clamp(0.5 * self.affect.valence + 0.5 * arrived.valence,
                                         -1.0, 1.0)}
            )
        self.last_anticipation = None
        ahead = self.anticipation.feeling(self.tick_no)
        if ahead is not None:
            dv, da, emo = ahead
            self.affect = self.affect.model_copy(
                update={
                    "valence": clamp(self.affect.valence + dv, -1.0, 1.0),
                    "arousal": clamp(self.affect.arousal + da),
                    "emotion": emo if abs(dv) >= 0.12 else self.affect.emotion,
                }
            )
            looming = self.anticipation.looming(self.tick_no)
            if looming is not None:
                self.last_anticipation = (looming.description, emo)
        self.needs.step(
            novelty=percept.novelty,
            arousal=self.affect.arousal,
            social=bool(present),
            valence=self.affect.valence,
        )
        # 3c. And let this lived moment slowly reshape who she is — the running
        #     tone of experience nudging her disposition (temperament drift).
        self.temperament.drift(
            novelty=percept.novelty,
            valence=self.affect.valence,
            arousal=self.affect.arousal,
            control=self._appraisal.control,
        )

        # 3d. Frustration & anger: an intention that keeps being blocked stokes
        #     frustration; once it boils over, a bad blocked moment becomes anger
        #     — unpleasant and activating, but oriented toward pushing back rather
        #     than withdrawing — and it re-charges the thwarted goal (persistence).
        self.last_anger = False
        self.frustration.update(
            has_goal=bool(self.goals.active()),
            goal_congruence=self._appraisal.goal_congruence,
        )
        if self.frustration.angry and self.affect.valence < 0.0:
            self.affect = self.affect.model_copy(
                update={
                    "emotion": Emotion.ANGER,
                    "arousal": clamp(self.affect.arousal + 0.15),
                }
            )
            top = self.goals.top()
            if top is not None:
                top.urgency = clamp(top.urgency + 0.2)  # anger fuels the pursuit
            self.last_anger = True

        # 4. Attention competition over candidate contents — but first, volition
        #    gets a say: she can spend effort to hold focus on what she means to be
        #    doing when something flashier is pulling her away (and, out of effort,
        #    she can't — the impulse wins).
        candidates = self._candidates(percept)
        goal = self.goals.top()
        # Self-control is the power to resist an *impulse* — when a strong feeling
        # is about to hijack her from what she means to be doing, she can spend
        # effort to hold the line. (It stays out of ordinary perception, so it
        # doesn't dampen her curiosity about the world.)
        leader = max(candidates, key=lambda c: c.salience)
        impulse = leader.source is ContentSource.FEELING
        if goal is not None and impulse:
            goal_tokens = set(tokenize(goal.description))
            relevant = [
                c.source is not ContentSource.FEELING
                and (
                    bool(set(tokenize(c.content)) & goal_tokens)
                    or c.content.startswith("my intention to")
                )
                for c in candidates
            ]
            self.last_effort = self.volition.focus(candidates, relevant)
        else:
            self.volition.recover()
            self.last_effort = False
        winner, also = self.attention.select(candidates, self.affect.arousal)
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

        # 6b. Self-conscious feeling: measure her conduct against her own
        #     standards. Following through breeds pride; letting go, disappointment.
        #     This reflective appraisal colours the feeling she carries onward.
        if any(event == "resolved" for event, _ in self.last_goal_events):
            self.frustration.relieve()  # getting through vents the pressure

        self.last_self_judgment = self.conscience.judge(self.last_goal_events)
        if self.last_self_judgment is not None:
            j = self.last_self_judgment
            self.affect = self.affect.model_copy(
                update={
                    "valence": clamp(0.5 * self.affect.valence + 0.5 * j.valence, -1.0, 1.0),
                    "arousal": clamp(self.affect.arousal + 0.1),
                    "emotion": j.emotion,
                }
            )
            self.self_model.affect = self.affect  # keep introspection consistent

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
        # Missing a loved one can well up on its own — a longing intrudes.
        if self.longing is not None:
            name, ache = self.longing
            candidates.append(
                Candidate(
                    content=f"how much I miss @{name}",
                    source=ContentSource.FEELING,
                    salience=clamp(0.3 + 0.5 * ache),
                )
            )
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
