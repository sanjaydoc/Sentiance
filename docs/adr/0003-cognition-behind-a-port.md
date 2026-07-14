# ADR 0003 — "Thinking" lives behind a Cognition port

- **Status:** Accepted
- **Date:** 2026-07-14

## Context

The mind needs a faculty that *deliberates*: given the current conscious moment
and self-model, decide the next inner thought or action. This is exactly where a
large language model would shine — but we also want the architecture to run
fully offline, deterministically, and be testable in CI without network or keys.

## Decision

Define a `Cognition` **port** — `deliberate(moment, source, self_model, memory)
→ Stimulus | None`. Provide two adapters:

- `SimulatedCognition` — deterministic, offline, template-driven by emotion and
  drives. The default; makes the whole system runnable and testable.
- `LLMCognition` — an Anthropic-backed inner monologue. It composes a prompt
  from the self-model + affect + drives + narrative and calls Claude
  (default `claude-opus-4-8`) for the mind's next private thought. The client is
  built lazily, so the package imports without the `anthropic` package or a key.
  Selected via `SENTIANCE_COGNITION_BACKEND=llm`.
- `OllamaCognition` — the same prompt against a **local** model served by Ollama
  (e.g. `qwen2.5:7b`), over Ollama's native `/api/chat` using `httpx`. No API key,
  no data leaves the machine, no extra dependency. Selected via
  `SENTIANCE_COGNITION_BACKEND=ollama`.

All three share one prompt builder and degrade gracefully: any failure to reach
the model (no key/server, network error, refusal) falls back to a deterministic
voice, so the cognitive cycle never stalls.

## Consequences

- The cognitive cycle, tests, and demo need no LLM. CI is hermetic.
- Upgrading to an LLM inner monologue is a one-line adapter swap; nothing else
  changes.
- The port keeps the LLM *inside* the architecture (as one faculty among many
  with a self-model, affect, and memory around it) rather than making the whole
  mind "an LLM with extra steps."
