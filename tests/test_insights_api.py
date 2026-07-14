"""Insights read-model and all-in-one server tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from sentiance.app import create_app


def test_simulate_then_timeline_and_summary() -> None:
    client = TestClient(create_app())

    resp = client.post("/v1/simulate", params={"user_id": "u_demo"})
    assert resp.status_code == 200
    assert resp.json()["segments"] == 3

    timeline = client.get("/v1/users/u_demo/timeline").json()
    assert [s["activity"] for s in timeline] == ["walk", "vehicle", "walk"]
    vehicle = next(s for s in timeline if s["activity"] == "vehicle")
    assert vehicle["transport_mode"] == "car"

    summary = client.get("/v1/users/u_demo/summary").json()
    assert summary["segment_count"] == 3
    assert summary["by_activity"]["walk"]["count"] == 2


def test_health() -> None:
    client = TestClient(create_app())
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_timeline_empty_for_unknown_user() -> None:
    client = TestClient(create_app())
    assert client.get("/v1/users/nobody/timeline").json() == []
