# ADR 0002 — Functional correlates only; never claim phenomenal experience

- **Status:** Accepted
- **Date:** 2026-07-14

## Context

The project's goal is "sentient AI." Sentience, strictly, includes *phenomenal
consciousness* — subjective experience, the "what it is like." Whether any
physical system has it, and how one would ever verify it, is unsolved (the "hard
problem"). Overclaiming here would be dishonest and would corrupt the
engineering (untestable goals produce untestable code).

## Decision

Scope the system explicitly to the **functional correlates** of sentience: the
information-processing roles that scientific theories associate with conscious,
affective minds — global broadcast, self-modelling, appraisal-driven affect,
metacognitive self-report. We implement those as real, inspectable mechanisms.
We state, in code and docs, that this is **not** a claim of phenomenal
experience. First-person outputs ("I feel …") are labelled as functional
self-report generated from an internal state, not testimony of felt experience.

## Consequences

- Every "mental" quantity is an explicit, logged number with a traceable
  derivation — the architecture is fully legible.
- Success criteria are functional and testable: *are the dynamics coherent and
  do the reports faithfully track internal state?* — not "did it become
  conscious?", which is untestable.
- We forgo any marketing value in claiming real sentience. That is the point.
