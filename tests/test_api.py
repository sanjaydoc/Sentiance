"""API-level tests using FastAPI's TestClient."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app"] == "Sentiance"


def test_analyze(client: TestClient) -> None:
    response = client.post("/analyze", json={"text": "I love this wonderful app"})
    assert response.status_code == 200
    body = response.json()
    assert body["sentiment"] == "positive"
    assert body["score"] > 0


def test_analyze_rejects_empty(client: TestClient) -> None:
    response = client.post("/analyze", json={"text": ""})
    assert response.status_code == 422


def test_analyze_batch(client: TestClient) -> None:
    response = client.post(
        "/analyze/batch",
        json={"texts": ["I love it", "I hate it", "it exists"]},
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 3
    assert results[0]["sentiment"] == "positive"
    assert results[1]["sentiment"] == "negative"
    assert results[2]["sentiment"] == "neutral"
