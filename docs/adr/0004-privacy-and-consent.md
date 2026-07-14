# ADR 0004 — Privacy-first: pseudonymity, consent-at-ingest, edge path

- **Status:** Accepted
- **Date:** 2026-07-14

## Context

The platform processes location and motion — among the most sensitive personal
data. Regulatory (GDPR) and ethical requirements demand data minimization,
purpose limitation, and user control. This must be structural, not bolted on.

## Decision

1. **Pseudonymous identifiers only.** Events carry `user_id` / `device_id`
   opaque tokens. No names, emails, or raw device identifiers flow through the
   pipeline. Re-identification lives in a separate, access-controlled service
   outside this data plane.
2. **Consent enforced at ingestion.** Each batch carries the consent scope in
   force at capture time. The gateway drops or restricts processing for scopes
   the user has not granted — nothing unauthorized ever reaches the bus.
3. **Multi-tenant isolation.** `tenant_id` on every event; stores enforce
   row-level isolation.
4. **Edge/feature path.** Because features are computable on-device (ADR-0003),
   the SDK may submit `features.window` directly, so **raw signal need never
   leave the device**. Downstream stages are identical either way.
5. **Data minimization + TTL.** Raw batches in cold storage have a short TTL;
   long-lived state is the derived, lower-resolution segment timeline.

## Consequences

- Privacy properties are enforced by the architecture, not policy alone.
- The edge path trades device CPU for a dramatically smaller privacy surface.
- Re-identification indirection adds operational steps for legitimate lookups;
  accepted as the cost of minimizing the sensitive data plane.
