"""Tests for competitor discovery stubs."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_find_competitors_returns_200_and_structure() -> None:
    payload = {"query": "project management saas", "max_results": 5}
    response = client.post("/find-competitors", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == payload["query"]
    assert isinstance(data["candidates"], list)
    assert len(data["candidates"]) >= 1
    first = data["candidates"][0]
    assert "url" in first
    assert "title" in first
    assert "snippet" in first
