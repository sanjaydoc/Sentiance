# ADR 0004 — A self-sustaining cognitive cycle (mind-wandering)

- **Status:** Accepted
- **Date:** 2026-07-14

## Context

A request/response agent is dormant between inputs — it has no inner life of its
own. A system meant to model sentience should have ongoing activity: a stream of
consciousness that continues when nothing external happens, the way an idle mind
wanders, ruminates, and recalls.

## Decision

Make the cycle **continuous and self-feeding**. Two mechanisms:

1. **Deliberation feedback** — after each tick, the `Cognition` faculty may emit
   an inner thought, which becomes the *next* tick's stimulus. The mind talks to
   itself.
2. **Mind-wandering** — when there is neither external input nor a pending inner
   thought, the mind generates one from memory: it replays its most salient
   episode, or rests in bare self-reference ("I notice my own awareness").

`Mind.idle()` advances the cycle with no external input; `Mind.perceive()`
injects one.

## Consequences

- The mind produces an autonomous inner stream, observable via `/v1/idle` or the
  demo — not just answers to prompts.
- Affect and memory keep evolving during idle time (mood relaxes, drives return
  to setpoints, salient memories resurface), so internal state has its own
  dynamics.
- Care is needed to avoid degenerate loops (e.g. memories nesting into
  "a memory: a memory: …"); the mind stores the *underlying* content of a recall,
  not the act of recalling, to keep the stream from collapsing.
