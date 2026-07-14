"""Ingestion use-case: validate consent, deduplicate, publish, archive.

Kept free of HTTP concerns so it is unit-testable and reusable by both the
FastAPI gateway and the in-process dev server (ADR-0001).
"""

from __future__ import annotations

from dataclasses import dataclass

from sentiance.core.bus.base import EventBus
from sentiance.core.schemas import TOPIC_SENSOR_RAW, ConsentScope, SensorBatch


@dataclass(slots=True)
class IngestResult:
    accepted: bool
    reason: str
    event_id: str | None = None


class IngestionService:
    """Enforces consent + idempotency, then publishes to ``sensor.raw``."""

    def __init__(
        self,
        bus: EventBus,
        required_consent: tuple[ConsentScope, ...] = (ConsentScope.MOTION,),
    ) -> None:
        self.bus = bus
        self.required_consent = required_consent
        self._seen: set[tuple[str, str]] = set()  # (device_id, batch_id)

    def ingest(self, batch: SensorBatch) -> IngestResult:
        # Consent enforced at the edge — nothing unauthorized reaches the bus.
        missing = [c for c in self.required_consent if c not in batch.consent]
        if missing:
            names = ", ".join(sorted(c.value for c in missing))
            return IngestResult(False, f"missing consent: {names}")

        # Idempotency on (device_id, batch_id) — safe retries (ADR-0002).
        dedup_key = (batch.device_id, batch.batch_id)
        if dedup_key in self._seen:
            return IngestResult(True, "duplicate", event_id=batch.event_id)
        self._seen.add(dedup_key)

        # (Production also archives the raw batch to cold storage here.)
        self.bus.publish(TOPIC_SENSOR_RAW, key=batch.device_id, value=batch)
        return IngestResult(True, "accepted", event_id=batch.event_id)
