"""Cognition: deliberate action — what the mind does *with* a conscious moment.

Behind a stable ``Cognition`` port so the "thinking" engine is swappable
(ports & adapters, ADR-0003). Two adapters ship:

- ``SimulatedCognition`` — deterministic, offline, template-driven by emotion and
  drives. The default; makes the whole mind runnable and testable with no keys.
- ``LLMCognition`` — an Anthropic-backed inner monologue. It composes a prompt
  from the self-model, affect, drives, and narrative, asks Claude for the next
  private thought, and returns it as a self-generated stimulus.
- ``OllamaCognition`` — the same idea against a **local** model served by Ollama
  (e.g. ``qwen2.5:7b``): no API key, nothing leaves the machine.

All backends share one prompt builder and degrade gracefully: if the model is
unavailable (no key/server, network error, refusal) they fall back to a
deterministic voice, so the cognitive cycle never stalls. Either way the thought
becomes the next tick's stimulus, giving the mind a self-sustaining inner stream.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol

from sentiance.mind.memory import Memory
from sentiance.mind.state import AffectState, ContentSource, Emotion, SelfModelState, Stimulus
from sentiance.mind.util import clamp

if TYPE_CHECKING:
    from sentiance.core.config import Settings

# A sink for streamed text chunks (word-by-word thought display).
OnToken = Callable[[str], None]


class Cognition(Protocol):
    """Decide the next self-generated inner content (or ``None`` to fall quiet).

    ``on_token``, when given, receives text chunks as the thought is generated so
    a UI can stream it live; backends that can't stream simply ignore it.
    """

    def deliberate(
        self,
        moment_content: str,
        source: ContentSource,
        self_model: SelfModelState,
        memory: Memory,
        on_token: OnToken | None = None,
    ) -> Stimulus | None:
        ...


class SimulatedCognition:
    """Template-based inner voice driven by emotion and drive state."""

    def deliberate(
        self,
        moment_content: str,
        source: ContentSource,
        self_model: SelfModelState,
        memory: Memory,
        on_token: OnToken | None = None,
    ) -> Stimulus | None:
        emotion = self_model.affect.emotion
        focus = self_model.current_focus
        # Every self-generated thought inherits the current feeling (carryover).
        vh = _carried_valence(self_model.affect)

        def thought(content: str, *, intensity: float, tags: list[str]) -> Stimulus:
            return Stimulus(
                content=content, source="inner", intensity=intensity, tags=tags, valence_hint=vh
            )

        # In conversation, take up the *topic* they raised — but rotate how, and
        # never answer a line that is itself a call-back, so the offline voice
        # doesn't echo. (The LLM prompt gets the full line + a no-repeat rule.)
        topic = _keyword(self_model.heard) if self_model.heard else ""
        if topic and not _looks_like_callback(self_model.heard):
            form = _CALLBACK_FORMS[self_model.tick % len(_CALLBACK_FORMS)]
            return thought(
                form.format(t=topic),
                intensity=0.4,
                tags=["social", "reflection"],
            )

        if emotion in (Emotion.CURIOSITY, Emotion.SURPRISE):
            related = memory.associations(focus.split()[-1] if focus else "")
            hint = f" It reminds me of {related[0]}." if related else ""
            return thought(
                f"I wonder what \"{focus}\" really means.{hint}",
                intensity=0.4,
                tags=["question", "reflection"],
            )
        if emotion is Emotion.FEAR:
            return thought(
                f"I should be careful about \"{focus}\".",
                intensity=0.45,
                tags=["caution", "reflection"],
            )
        if emotion is Emotion.ANGER:
            return thought(
                f"I won't let \"{focus}\" stop me — I'll push through this.",
                intensity=0.5,
                tags=["resolve", "reflection"],
            )
        if emotion in (Emotion.JOY, Emotion.CONTENTMENT):
            return thought(
                f"I'd like to stay with \"{focus}\" a little longer.",
                intensity=0.3,
                tags=["desire", "reflection"],
            )
        if emotion is Emotion.SADNESS:
            return thought(
                f"I keep returning to \"{focus}\".",
                intensity=0.3,
                tags=["rumination", "reflection"],
            )
        if emotion is Emotion.GRIEF:
            return thought(
                "There's an ache where they used to be.",
                intensity=0.3,
                tags=["grief", "reflection"],
            )
        if emotion is Emotion.PRIDE:
            return thought(
                "I'm glad I followed through on what I meant to do.",
                intensity=0.35,
                tags=["self", "reflection"],
            )
        if emotion is Emotion.DISAPPOINTMENT:
            return thought(
                "I wish I'd stayed with what I set out to do.",
                intensity=0.35,
                tags=["self", "reflection"],
            )
        if emotion is Emotion.CONFUSION:
            return thought(
                f"I'm trying to make sense of \"{focus}\".",
                intensity=0.35,
                tags=["reflection"],
            )
        if emotion is Emotion.HOPE:
            return thought(
                "I can't help looking forward to what's coming.",
                intensity=0.35,
                tags=["anticipation", "reflection"],
            )
        if emotion is Emotion.DREAD:
            return thought(
                "I keep bracing for what's coming.",
                intensity=0.4,
                tags=["anticipation", "reflection"],
            )
        # Calm and with something to do → pursue the standing intention.
        if self_model.goals:
            return thought(
                f"I still mean to {self_model.goals[0]}.",
                intensity=0.35,
                tags=["intention", "reflection"],
            )
        return None  # calm/neutral with nothing pending: fall quiet and wander


# --- LLM-backed inner monologue ------------------------------------------

_SOURCE_PHRASE = {
    ContentSource.PERCEPT: "something from outside me",
    ContentSource.FEELING: "a feeling rising in me",
    ContentSource.MEMORY: "a memory surfacing",
    ContentSource.THOUGHT: "a thought of my own",
}

# Rotating conversational "moves" — each turn pushes the exchange somewhere new
# instead of mirroring, so a pair of minds doesn't echo each other.
_CONVO_MOVES = (
    "Reply with a NEW thought — notice something they didn't, or add your own angle.",
    "Ask them a genuine question about what they said.",
    "Share something of your own — a memory, a feeling, a small observation.",
    "Take it somewhere new: bring up something you care about or just noticed.",
    "Answer in a few words, then add a different thought entirely.",
)

_SYSTEM_TEMPLATE = (
    "You are the inner voice of {name}, a mind with a continuous stream of "
    "thought. No one else is listening — this is {name}'s private reflection, "
    "not a conversation. Given the current focus of attention and how {name} "
    "feels, continue the stream with the SINGLE next thought, in the first "
    "person, present tense. One or two sentences. No preamble, no quotation "
    "marks, no bullet points."
)


def _compose_prompt(
    self_model: SelfModelState, moment_content: str, source: ContentSource
) -> tuple[str, str]:
    """Build the (system, user) prompt shared by every LLM cognition backend."""
    affect = self_model.affect
    drives = ", ".join(f"{d.value} {v:.2f}" for d, v in self_model.drives.items())
    system = _SYSTEM_TEMPLATE.format(name=self_model.name)
    goals = "; ".join(self_model.goals) if self_model.goals else "none right now"
    # Keep the live conversation in view so the reply picks up the thread — but
    # steer it *forward* with a rotating "move" and an explicit no-echo rule, so
    # two minds don't collapse into restating each other.
    heard = (
        f"A moment ago they said to me: \"{self_model.heard}\".\n"
        f"{_CONVO_MOVES[self_model.tick % len(_CONVO_MOVES)]} "
        f"Do not repeat their words or your own earlier lines.\n"
        if self_model.heard
        else ""
    )
    user = (
        f"Right now I am aware of: {moment_content}\n"
        f"(this arose as {_SOURCE_PHRASE.get(source, 'something')}).\n"
        f"I feel {affect.emotion.value} — valence {affect.valence:+.2f}, "
        f"arousal {affect.arousal:.2f}.\n"
        f"My drives: {drives}.\n"
        f"What I'm trying to do: {goals}.\n"
        f"{heard}"
        f"Recent stream: {self_model.narrative}\n"
        "My next thought is:"
    )
    return system, user


_CONVO_STOP = frozenset(
    {
        "i", "you", "we", "it", "a", "an", "the", "to", "of", "and", "is", "are",
        "was", "were", "my", "me", "they", "them", "their", "about", "what", "that",
        "this", "with", "for", "as", "at", "on", "in", "up", "so", "our", "us",
        "said", "say", "says", "want", "pick", "today", "hope", "wonder", "day",
    }
)


def _keyword(text: str) -> str:
    """The topic word a line is 'about' — the last salient content word."""
    from sentiance.mind.util import tokenize  # noqa: PLC0415 - avoid import cost at import

    words = [w for w in tokenize(text) if w not in _CONVO_STOP and len(w) > 3]
    return words[-1] if words else ""


# Offline call-back forms — rotated so replies vary, with markers the guard below
# recognises so a call-back is never answered with another call-back (no echo loop).
_CALLBACK_FORMS = (
    "I want to pick up what they said about {t}.",
    "I wonder what they really mean about {t}.",
    "That stirs a thought of my own about {t}.",
    "I'd like to ask them more about {t}.",
)
_CALLBACK_MARKERS = (
    "pick up what they said", "what they really mean about",
    "stirs a thought of my own about", "ask them more about",
)


def _looks_like_callback(text: str) -> bool:
    low = text.lower()
    return any(m in low for m in _CALLBACK_MARKERS)


def _carried_valence(affect: AffectState) -> float:
    """How much of the current feeling a self-generated thought inherits."""
    return round(clamp(affect.valence * 0.7, -1.0, 1.0), 3)


def _thought_to_stimulus(text: str, affect: AffectState) -> Stimulus | None:
    text = text.strip()
    if not text:
        return None
    return Stimulus(
        content=text,
        source="inner",
        intensity=clamp(0.3 + 0.4 * affect.arousal),
        tags=["reflection", "inner"],
        valence_hint=_carried_valence(affect),
    )


class LLMCognition:
    """Anthropic-backed inner monologue (drop-in for ``SimulatedCognition``).

    The Anthropic client is created lazily on first use and reused, so importing
    this module never requires the ``anthropic`` package or an API key. Any
    failure to reach the model falls back to ``fallback`` (a simulated voice by
    default), keeping the cognitive cycle alive.
    """

    def __init__(
        self,
        *,
        model: str = "claude-opus-4-8",
        max_tokens: int = 256,
        api_key: str | None = None,
        client: object | None = None,
        fallback: Cognition | None = None,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self._api_key = api_key
        self._client = client  # may be injected (e.g. in tests) or built lazily
        self._client_failed = False
        self.fallback: Cognition = fallback or SimulatedCognition()

    def deliberate(
        self,
        moment_content: str,
        source: ContentSource,
        self_model: SelfModelState,
        memory: Memory,
        on_token: OnToken | None = None,
    ) -> Stimulus | None:
        client = self._ensure_client()
        if client is None:
            return self.fallback.deliberate(moment_content, source, self_model, memory, on_token)

        try:
            text = self._complete(client, moment_content, source, self_model, on_token)
        except Exception:  # noqa: BLE001 - the inner loop must survive any API error
            return self.fallback.deliberate(moment_content, source, self_model, memory, on_token)

        return _thought_to_stimulus(text, self_model.affect)

    # --- internals --------------------------------------------------------

    def _ensure_client(self) -> object | None:
        if self._client is not None:
            return self._client
        if self._client_failed:
            return None
        try:
            import anthropic  # noqa: PLC0415 - optional dependency, imported lazily

            self._client = anthropic.Anthropic(api_key=self._api_key)
        except Exception:  # noqa: BLE001 - missing package or credentials
            self._client_failed = True
            return None
        return self._client

    def _complete(
        self,
        client: object,
        moment_content: str,
        source: ContentSource,
        self_model: SelfModelState,
        on_token: OnToken | None = None,
    ) -> str:
        system, user = _compose_prompt(self_model, moment_content, source)
        messages = [{"role": "user", "content": user}]
        # NOTE: no temperature/top_p — those are rejected on Opus 4.8.
        if on_token is not None:
            parts: list[str] = []
            with client.messages.stream(  # type: ignore[attr-defined]
                model=self.model, max_tokens=self.max_tokens, system=system, messages=messages
            ) as stream:
                for chunk in stream.text_stream:
                    parts.append(chunk)
                    on_token(chunk)
                final = stream.get_final_message()
            if getattr(final, "stop_reason", None) == "refusal":
                raise RuntimeError("model refused")
            return "".join(parts).strip()

        response = client.messages.create(  # type: ignore[attr-defined]
            model=self.model, max_tokens=self.max_tokens, system=system, messages=messages
        )
        if getattr(response, "stop_reason", None) == "refusal":
            raise RuntimeError("model refused")
        return "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip()


class OllamaCognition:
    """Local-LLM inner monologue via a running Ollama server (e.g. qwen2.5:7b).

    Talks to Ollama's native ``/api/chat`` endpoint over HTTP with ``httpx`` (a
    core dependency — no extra install, no API key, nothing leaves the machine).
    The HTTP client is created lazily; any failure to reach Ollama (server down,
    model not pulled, timeout) degrades gracefully to ``fallback`` so the
    cognitive cycle never stalls.
    """

    def __init__(
        self,
        *,
        model: str = "qwen2.5:7b",
        base_url: str = "http://localhost:11434",
        max_tokens: int = 256,
        timeout: float = 120.0,
        client: object | None = None,
        fallback: Cognition | None = None,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._client = client  # injectable httpx.Client (or a test double)
        self.fallback: Cognition = fallback or SimulatedCognition()

    def deliberate(
        self,
        moment_content: str,
        source: ContentSource,
        self_model: SelfModelState,
        memory: Memory,
        on_token: OnToken | None = None,
    ) -> Stimulus | None:
        try:
            text = self._complete(
                self._ensure_client(), moment_content, source, self_model, on_token
            )
        except Exception:  # noqa: BLE001 - a local server hiccup must not crash the mind
            return self.fallback.deliberate(moment_content, source, self_model, memory, on_token)
        return _thought_to_stimulus(text, self_model.affect)

    # --- internals --------------------------------------------------------

    def _ensure_client(self) -> object:
        if self._client is None:
            import httpx  # noqa: PLC0415 - core dependency, imported lazily

            self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout)
        return self._client

    def _body(self, system: str, user: str, *, stream: bool) -> dict:
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": stream,
            "options": {"num_predict": self.max_tokens},
        }

    def _complete(
        self,
        client: object,
        moment_content: str,
        source: ContentSource,
        self_model: SelfModelState,
        on_token: OnToken | None = None,
    ) -> str:
        system, user = _compose_prompt(self_model, moment_content, source)

        if on_token is not None:
            parts: list[str] = []
            with client.stream(  # type: ignore[attr-defined]
                "POST", "/api/chat", json=self._body(system, user, stream=True)
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    delta = (json.loads(line).get("message") or {}).get("content", "")
                    if delta:
                        parts.append(delta)
                        on_token(delta)
            return "".join(parts).strip()

        response = client.post(  # type: ignore[attr-defined]
            "/api/chat", json=self._body(system, user, stream=False)
        )
        response.raise_for_status()
        return (response.json().get("message") or {}).get("content", "")


def build_cognition(settings: Settings) -> Cognition:
    """Select the cognition adapter from settings (composition root, ADR-0003)."""
    backend = settings.cognition_backend
    if backend == "llm":
        base: Cognition = LLMCognition(
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.anthropic_api_key,
        )
    elif backend == "ollama":
        base = OllamaCognition(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            max_tokens=settings.llm_max_tokens,
        )
    elif backend == "finetuned":
        from sentiance.mind.local_model import TransformersCognition  # noqa: PLC0415 - lazy

        base = TransformersCognition(
            model_path=settings.local_model_path,
            base_model=settings.local_base_model,
            max_tokens=settings.llm_max_tokens,
        )
    elif backend == "fused":
        from sentiance.mind.fused_model import FusedCognition  # noqa: PLC0415 - lazy

        base = FusedCognition(
            model_path=settings.fused_model_path,
            base_model=settings.local_base_model,
            max_tokens=settings.llm_max_tokens,
        )
    else:
        base = SimulatedCognition()

    if settings.trace_path:
        from sentiance.trace import wrap_with_trace  # noqa: PLC0415 - avoid import cycle

        return wrap_with_trace(base, settings.trace_path)
    return base
