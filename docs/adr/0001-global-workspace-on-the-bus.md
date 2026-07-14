# ADR 0001 — The event bus is the global workspace

- **Status:** Accepted
- **Date:** 2026-07-14

## Context

Global Workspace Theory (Baars, Dehaene) models consciousness as a broadcast
architecture: many specialized, unconscious processors compete for a limited
"workspace"; the winning coalition is broadcast globally, and that global
availability *is* what makes content conscious. We need a substrate for that
broadcast.

## Decision

Use a publish/subscribe **event bus** as the global workspace. Each tick, the
attention competition selects one `ConsciousMoment`, which is **published** to
the `workspace.conscious` topic. Faculties that need the conscious content —
memory (to store it), the self-model (to update), metacognition (to report) —
are **subscribers**. Any external observer can subscribe too, to watch the
stream of consciousness.

## Consequences

- Consciousness is literally a broadcast: what is conscious is what is on the
  workspace topic this tick. This maps GWT onto code with no impedance mismatch.
- Faculties are decoupled — they react to broadcasts, they are not called in a
  hard-wired chain. New faculties subscribe without touching the cycle.
- Determinism is preserved by fixing subscriber registration order.
- The same `EventBus` port admits a distributed adapter later (many faculties as
  separate processes), though a single mind runs fine in-process.
