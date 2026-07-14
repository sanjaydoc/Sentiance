"""Ingestion service and gateway tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from sentiance.core.bus.memory import InMemoryEventBus
from sentiance.core.schemas import TOPIC_SENSOR_RAW, Activity, ConsentScope
from sentiance.ingestion.app import create_ingestion_app
from sentiance.ingestion.service import IngestionService
from sentiance.simulation.generator import simulate_activity


def test_ingest_publishes_when_consent_present(bus: InMemoryEventBus) -> None:
    svc = IngestionService(bus)
    batch = simulate_activity(Activity.WALK, duration_s=10.0)
    result = svc.ingest(batch)
    assert result.accepted
    assert len(bus.messages_on(TOPIC_SENSOR_RAW)) == 1


def test_ingest_rejects_missing_consent(bus: InMemoryEventBus) -> None:
    svc = IngestionService(bus)
    batch = simulate_activity(Activity.WALK, duration_s=10.0)
    batch.consent = [ConsentScope.LOCATION]  # motion consent missing
    result = svc.ingest(batch)
    assert not result.accepted
    assert "motion" in result.reason
    assert bus.messages_on(TOPIC_SENSOR_RAW) == []


def test_ingest_is_idempotent(bus: InMemoryEventBus) -> None:
    svc = IngestionService(bus)
    batch = simulate_activity(Activity.WALK, duration_s=10.0)
    svc.ingest(batch)
    svc.ingest(batch)  # same (device_id, batch_id)
    assert len(bus.messages_on(TOPIC_SENSOR_RAW)) == 1


def test_gateway_requires_api_key(bus: InMemoryEventBus) -> None:
    client = TestClient(create_ingestion_app(bus))
    batch = simulate_activity(Activity.WALK, duration_s=10.0)
    # No X-API-Key header.
    resp = client.post("/v1/batches", json=batch.model_dump(mode="json"))
    assert resp.status_code == 422  # missing required header


def test_gateway_accepts_valid_batch(bus: InMemoryEventBus) -> None:
    client = TestClient(create_ingestion_app(bus))
    batch = simulate_activity(Activity.WALK, duration_s=10.0)
    resp = client.post(
        "/v1/batches",
        json=batch.model_dump(mode="json"),
        headers={"X-API-Key": "dev-key"},
    )
    assert resp.status_code == 200
    assert resp.json()["accepted"] is True


def test_gateway_rejects_bad_key(bus: InMemoryEventBus) -> None:
    client = TestClient(create_ingestion_app(bus))
    batch = simulate_activity(Activity.WALK, duration_s=10.0)
    resp = client.post(
        "/v1/batches",
        json=batch.model_dump(mode="json"),
        headers={"X-API-Key": "wrong"},
    )
    assert resp.status_code == 401
