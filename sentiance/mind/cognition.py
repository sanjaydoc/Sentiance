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

from typing import TYPE_CHECKING, Protocol

from sentiance.mind.memory import Memory
from sentiance.mind.state import ContentSource, Emotion, SelfModelState, Stimulus
from sentiance.mind.util import clamp

if TYPE_CHECKING:
    from sentiance.core.config import Settings


class Cognition(Protocol):
    """Decide the next self-generated inner content (or ``None`` to fall quiet)."""

    def deliberate(
        self, moment_content: str, source: ContentSource, self_model: SelfModelState, memory: Memory
    ) -> Stimulus | None:
        ...


class SimulatedCognition:
    """Template-based inner voice driven by emotion and drive state."""

    def deliberate(
        self, moment_content: str, source: ContentSource, self_model: SelfModelState, memory: Memory
    ) -> Stimulus | None:
        emotion = self_model.affect.emotion
        focus = self_model.current_focus

        if emotion in (Emotion.CURIOSITY, Emotion.SURPRISE):
            related = memory.associations(focus.split()[-1] if focus else "")
            hint = f" It reminds me of {related[0]}." if related else ""
            return Stimulus(
                content=f"I wonder what \"{focus}\" really means.{hint}",
                source="inner",
                intensity=0.4,
                tags=["question", "reflection"],
            )
        if emotion is Emotion.FEAR:
            return Stimulus(
                content=f"I should be careful about \"{focus}\".",
                source="inner",
                intensity=0.45,
                tags=["caution", "reflection"],
            )
        if emotion in (Emotion.JOY, Emotion.CONTENTMENT):
            return Stimulus(
                content=f"I'd like to stay with \"{focus}\" a little longer.",
                source="inner",
                intensity=0.3,
                tags=["desire", "reflection"],
                valence_hint=0.4,
            )
        if emotion is Emotion.SADNESS:
            return Stimulus(
                content=f"I keep returning to \"{focus}\".",
                source="inner",
                intensity=0.3,
                tags=["rumination", "reflection"],
                valence_hint=-0.3,
            )
        if emotion is Emotion.CONFUSION:
            return Stimulus(
                content=f"I'm trying to make sense of \"{focus}\".",
                source="inner",
                intensity=0.35,
                tags=["reflection"],
            )
        return None  # calm/neutral: let the mind fall quiet and wander


# --- LLM-backed inner monologue ------------------------------------------

_SOURCE_PHRASE = {
    ContentSource.PERCEPT: "something from outside me",
    ContentSource.FEELING: "a feeling rising in me",
    ContentSource.MEMORY: "a memory surfacing",
    ContentSource.THOUGHT: "a thought of my own",
}

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
    user = (
        f"Right now I am aware of: {moment_content}\n"
        f"(this arose as {_SOURCE_PHRASE.get(source, 'something')}).\n"
        f"I feel {affect.emotion.value} — valence {affect.valence:+.2f}, "
        f"arousal {affect.arousal:.2f}.\n"
        f"My drives: {drives}.\n"
        f"Recent stream: {self_model.narrative}\n"
        "My next thought is:"
    )
    return system, user


def _thought_to_stimulus(text: str, arousal: float) -> Stimulus | None:
    text = text.strip()
    if not text:
        return None
    return Stimulus(
        content=text,
        source="inner",
        intensity=clamp(0.3 + 0.4 * arousal),
        tags=["reflection", "inner"],
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
        self, moment_content: str, source: ContentSource, self_model: SelfModelState, memory: Memory
    ) -> Stimulus | None:
        client = self._ensure_client()
        if client is None:
            return self.fallback.deliberate(moment_content, source, self_model, memory)

        try:
            text = self._complete(client, moment_content, source, self_model)
        except Exception:  # noqa: BLE001 - the inner loop must survive any API error
            return self.fallback.deliberate(moment_content, source, self_model, memory)

        return _thought_to_stimulus(text, self_model.affect.arousal)

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
        self, client: object, moment_content: str, source: ContentSource, self_model: SelfModelState
    ) -> str:
        system, user = _compose_prompt(self_model, moment_content, source)
        # NOTE: no temperature/top_p — those are rejected on Opus 4.8.
        response = client.messages.create(  # type: ignore[attr-defined]
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
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
        self, moment_content: str, source: ContentSource, self_model: SelfModelState, memory: Memory
    ) -> Stimulus | None:
        try:
            text = self._complete(self._ensure_client(), moment_content, source, self_model)
        except Exception:  # noqa: BLE001 - a local server hiccup must not crash the mind
            return self.fallback.deliberate(moment_content, source, self_model, memory)
        return _thought_to_stimulus(text, self_model.affect.arousal)

    # --- internals --------------------------------------------------------

    def _ensure_client(self) -> object:
        if self._client is None:
            import httpx  # noqa: PLC0415 - core dependency, imported lazily

            self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout)
        return self._client

    def _complete(
        self, client: object, moment_content: str, source: ContentSource, self_model: SelfModelState
    ) -> str:
        system, user = _compose_prompt(self_model, moment_content, source)
        response = client.post(  # type: ignore[attr-defined]
            "/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
                "options": {"num_predict": self.max_tokens},
            },
        )
        response.raise_for_status()
        return (response.json().get("message") or {}).get("content", "")


def build_cognition(settings: Settings) -> Cognition:
    """Select the cognition adapter from settings (composition root, ADR-0003)."""
    backend = settings.cognition_backend
    if backend == "llm":
        return LLMCognition(
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.anthropic_api_key,
        )
    if backend == "ollama":
        return OllamaCognition(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            max_tokens=settings.llm_max_tokens,
        )
    return SimulatedCognition()
