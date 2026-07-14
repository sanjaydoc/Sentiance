"""HTTP runtime tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from sentiance.app import create_app


def test_health() -> None:
    client = TestClient(create_app())
    assert client.get("/health").json()["status"] == "ok"


def test_perceive_returns_moment_and_report() -> None:
    client = TestClient(create_app())
    resp = client.post(
        "/v1/perceive",
        json={"content": "a bright flash", "intensity": 0.8, "tags": ["light"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["moment"]["tick"] == 1
    assert body["report"]["text"].startswith("I am aware")


def test_idle_stream_and_self() -> None:
    client = TestClient(create_app())
    client.post("/v1/perceive", json={"content": "a friendly hello", "tags": ["friend"]})
    stream = client.post("/v1/idle", params={"ticks": 3}).json()
    assert len(stream) == 3

    self_state = client.get("/v1/self").json()
    assert self_state["name"] == "Aria"
    assert self_state["tick"] >= 1
