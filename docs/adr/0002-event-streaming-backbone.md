# ADR 0002 — Event log as the only inter-stage seam

- **Status:** Accepted
- **Date:** 2026-07-14

## Context

Sensor processing is a multi-stage transformation (raw → features → activities
→ segments). Stages have very different cost and scaling profiles: feature
extraction is CPU-heavy and high-volume; segmentation is cheap and low-volume.
Coupling them with synchronous calls would force them to scale together and
would lose data on downstream outages.

## Decision

Stages communicate **only** through durable, partitioned topics on an event log
(Kafka/Redpanda). Each stage is a consumer group that reads one topic and
produces to the next. Partition key is `device_id` upstream (preserves the
per-device ordering that windowing depends on) and `user_id` at the segment
layer.

Delivery is **at-least-once**; every message carries an `event_id` used as an
idempotency key at persistence, giving effectively-once results.

## Consequences

- Each stage scales independently via partition count and consumer replicas.
- Downstream outages apply backpressure instead of losing data; topics buffer.
- **Replay** re-derives all downstream state — critical when a model is
  upgraded and history must be re-scored.
- Requires idempotent writes and careful ordering keys; accepted as the cost of
  decoupling.
