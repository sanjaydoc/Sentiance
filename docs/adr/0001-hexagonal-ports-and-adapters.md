# ADR 0001 — Hexagonal core (ports & adapters)

- **Status:** Accepted
- **Date:** 2026-07-14

## Context

The platform must run in two very different environments: developer laptops and
CI (fast, no infrastructure) and production (Kafka/Redpanda + Postgres). We do
**not** want "mock" code paths that only exist in tests, because those diverge
from production and hide bugs.

## Decision

Structure the domain as a hexagon. The core (`sentiance/core`, `features`,
`recognition`) depends only on **ports** — abstract interfaces:

- `EventBus` — `publish(topic, message)` / `subscribe(topic, handler)`
- `SegmentRepository` — persistence of derived segments

Infrastructure lives in **adapters** that implement those ports:

- `InMemoryEventBus` / `KafkaEventBus`
- `InMemorySegmentRepository` / (Postgres adapter, specced)

Which adapter is used is a wiring decision made at the edge (`__main__`, service
startup), never in domain code.

## Consequences

- The identical pipeline code runs in-process for tests and against Kafka in
  prod. No production mocks.
- New infrastructure (e.g. Kinesis, PubSub) is a new adapter, not a rewrite.
- Slightly more indirection; justified by testability and portability.
