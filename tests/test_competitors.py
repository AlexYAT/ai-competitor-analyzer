"""Tests for competitor discovery (Brave mocked)."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_brave_client, get_settings
from app.clients.brave_client import BraveSearchClient
from app.core.config import Settings
from app.main import app
from app.models.enums import SiteType

_TEST_SETTINGS = Settings(
    BRAVE_API_KEY="test-key",
    BRAVE_BASE_URL="https://api.search.brave.com/res/v1/web/search",
    HTTP_TIMEOUT=20.0,
)


def _mock_brave_payload() -> dict[str, Any]:
    return {
        "web": {
            "results": [
                {"title": "Alpha", "url": "https://alpha.example/", "description": "First hit"},
                {
                    "title": "Duplicate URL",
                    "url": "https://alpha.example/",
                    "description": "",
                },
                {"title": "Beta", "url": "https://beta.example", "description": "Second"},
            ]
        }
    }


class _FakeBrave:
    def search_web(self, query: str, count: int = 10) -> dict[str, Any]:
        assert query
        assert count >= 1
        return _mock_brave_payload()


@pytest.fixture
def client():
    app.dependency_overrides[get_settings] = lambda: _TEST_SETTINGS
    app.dependency_overrides[get_brave_client] = lambda: _FakeBrave()  # type: ignore[return-value]
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_find_competitors_returns_200_and_structure(client: TestClient) -> None:
    payload = {
        "niche": "project management saas",
        "site_type": SiteType.landing.value,
        "region": "EU",
        "max_results": 5,
    }
    response = client.post("/find-competitors", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "query_used" in data
    assert isinstance(data["query_used"], str)
    assert "landing" in data["query_used"]
    assert "EU" in data["query_used"]

    assert data["raw_results_count"] == 3

    fr = data["filtered_results"]
    assert isinstance(fr, list)
    assert len(fr) == 2
    first = fr[0]
    assert first["title"]
    assert first["url"].startswith("http")
    assert first["source"] == "brave"
    assert first["site_type"] == SiteType.landing.value


def test_find_competitors_without_api_key() -> None:
    empty_settings = Settings(
        BRAVE_API_KEY="",
        BRAVE_BASE_URL="https://api.search.brave.com/res/v1/web/search",
        HTTP_TIMEOUT=20.0,
    )
    app.dependency_overrides[get_settings] = lambda: empty_settings
    app.dependency_overrides[get_brave_client] = lambda: BraveSearchClient(empty_settings)

    with TestClient(app) as test_client:
        payload = {
            "niche": "test",
            "site_type": SiteType.blog.value,
            "max_results": 3,
        }
        response = test_client.post("/find-competitors", json=payload)

    app.dependency_overrides.clear()

    assert response.status_code == 503
    assert "BRAVE_API_KEY" in response.json()["detail"]
