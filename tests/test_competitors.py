"""Tests for competitor discovery (Brave + optional LLM mocked)."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_brave_client, get_llm_client, get_settings
from app.clients.brave_client import BraveSearchClient
from app.core.config import Settings
from app.core.exceptions import ParsingError
from app.main import app
from app.models.enums import SiteType
from app.models.schemas import (
    CompetitorAnalysisResult,
    CompetitorCandidate,
    MarketReportItem,
    ParsedPageData,
    ReportDemoItemOk,
    ReportDemoResponse,
    ReportSummary,
)
from app.services import competitor_filter_service

_TEST_SETTINGS = Settings(
    BRAVE_API_KEY="test-key",
    BRAVE_BASE_URL="https://api.search.brave.com/res/v1/web/search",
    HTTP_TIMEOUT=20.0,
    OPENAI_API_KEY="",
    OPENAI_MODEL="gpt-4o-mini",
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


class _FakeLLM:
    def chat_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        return {"selected_indices": [1]}


@pytest.fixture
def client_no_llm():
    app.dependency_overrides[get_settings] = lambda: _TEST_SETTINGS
    app.dependency_overrides[get_brave_client] = lambda: _FakeBrave()  # type: ignore[return-value]
    app.dependency_overrides[get_llm_client] = lambda: _FakeLLM()  # type: ignore[return-value]
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def client_with_llm():
    settings = _TEST_SETTINGS.model_copy(update={"OPENAI_API_KEY": "sk-test"})
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_brave_client] = lambda: _FakeBrave()  # type: ignore[return-value]

    class SubsetLLM:
        def chat_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
            return {"selected_indices": [0]}

    app.dependency_overrides[get_llm_client] = lambda: SubsetLLM()  # type: ignore[return-value]
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_find_competitors_no_openai_key_uses_raw_candidates(client_no_llm: TestClient) -> None:
    payload = {
        "niche": "project management saas",
        "site_type": SiteType.landing.value,
        "region": "EU",
        "max_results": 5,
    }
    response = client_no_llm.post("/find-competitors", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "query_used" in data
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


def test_find_competitors_with_openai_key_applies_llm_filter(client_with_llm: TestClient) -> None:
    payload = {
        "niche": "yoga instructor",
        "site_type": SiteType.landing.value,
        "max_results": 5,
    }
    response = client_with_llm.post("/find-competitors", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["raw_results_count"] == 3
    fr = data["filtered_results"]
    assert len(fr) == 1
    assert fr[0]["url"] == "https://alpha.example/"
    assert fr[0]["source"] == "brave"


def test_find_competitors_without_brave_api_key() -> None:
    empty_settings = Settings(
        BRAVE_API_KEY="",
        BRAVE_BASE_URL="https://api.search.brave.com/res/v1/web/search",
        HTTP_TIMEOUT=20.0,
    )
    app.dependency_overrides[get_settings] = lambda: empty_settings
    app.dependency_overrides[get_brave_client] = lambda: BraveSearchClient(empty_settings)
    app.dependency_overrides[get_llm_client] = lambda: _FakeLLM()  # type: ignore[return-value]

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


def test_filter_competitors_with_llm_empty_candidates() -> None:
    assert (
        competitor_filter_service.filter_competitors_with_llm(
            _FakeLLM(), "n", SiteType.landing, None, []
        )
        == []
    )


@pytest.fixture
def client_with_openai():
    settings = _TEST_SETTINGS.model_copy(update={"OPENAI_API_KEY": "sk-test"})
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_brave_client] = lambda: _FakeBrave()  # type: ignore[return-value]
    app.dependency_overrides[get_llm_client] = lambda: _FakeLLM()  # type: ignore[return-value]
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_reportdemo_mocked(
    client_with_openai: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_build(
        urls: list[str],
        settings: Settings,
        llm: Any,
        *,
        lang: str = "ru",
    ) -> ReportDemoResponse:
        assert len(urls) == 2
        assert lang == "ru"
        items = [
            ReportDemoItemOk(
                url="https://a.example",
                analysis=MarketReportItem(
                    url="https://a.example",
                    final_url="https://a.example/",
                    title="A",
                    positioning="Pos A",
                    offer="Off A",
                    target_audience="TA",
                    strengths=["s1"],
                    weaknesses=["w1"],
                    design_score=5.0,
                    animation_potential=6.0,
                    summary="Sum A",
                ),
            ),
            ReportDemoItemOk(
                url="https://b.example",
                analysis=MarketReportItem(
                    url="https://b.example",
                    final_url="https://b.example/",
                    title="B",
                    positioning="Pos B",
                    offer="Off B",
                    target_audience="TB",
                    strengths=["s2"],
                    weaknesses=["w2"],
                    design_score=7.0,
                    animation_potential=4.0,
                    summary="Sum B",
                ),
            ),
        ]
        summary = ReportSummary(
            market_summary="Market overview text.",
            common_strengths=["Shared strength"],
            common_weaknesses=["Shared weakness"],
            differentiation_opportunities=["Do X differently"],
        )
        return ReportDemoResponse(items=items, summary=summary)

    monkeypatch.setattr("app.api.routes.competitors.build_market_report", fake_build)
    response = client_with_openai.post(
        "/reportdemo",
        json={"urls": ["https://a.example", "https://b.example"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    sm = data["summary"]
    assert sm["market_summary"] == "Market overview text."
    assert sm["common_strengths"] == ["Shared strength"]
    assert sm["common_weaknesses"] == ["Shared weakness"]
    assert sm["differentiation_opportunities"] == ["Do X differently"]


def test_reportdemo_accepts_lang_and_passes_to_build(
    client_with_openai: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, str] = {}

    def fake_build(
        urls: list[str],
        settings: Settings,
        llm: Any,
        *,
        lang: str = "ru",
    ) -> ReportDemoResponse:
        captured["lang"] = lang
        return ReportDemoResponse(
            items=[],
            summary=ReportSummary(
                market_summary="—",
                common_strengths=[],
                common_weaknesses=[],
                differentiation_opportunities=[],
            ),
        )

    monkeypatch.setattr("app.api.routes.competitors.build_market_report", fake_build)
    r1 = client_with_openai.post("/reportdemo", json={"urls": ["https://a.example"], "lang": "en"})
    assert r1.status_code == 200
    assert captured["lang"] == "en"

    r2 = client_with_openai.post("/reportdemo", json={"urls": ["https://a.example"]})
    assert r2.status_code == 200
    assert captured["lang"] == "ru"


def test_reportdemo_partial_parse_failure(client_with_openai: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    parsed_ok = ParsedPageData(
        requested_url="https://good.example/",
        final_url="https://good.example/",
        title="G",
        meta_description=None,
        h1="H",
        visible_text="body",
        screenshot_path=None,
    )

    def fake_parse(u: str, settings: Settings) -> ParsedPageData:
        if "bad.example" in u:
            raise ParsingError("The page took too long to load.", reason_code="timeout")
        return parsed_ok

    def fake_analyze(
        llm: Any,
        p: ParsedPageData,
        *,
        output_lang: str | None = None,
    ) -> CompetitorAnalysisResult:
        assert p.title == "G"
        return CompetitorAnalysisResult(
            url=p.requested_url,
            final_url=p.final_url,
            title=p.title,
            positioning="p",
            offer="o",
            target_audience="t",
            strengths=["s"],
            weaknesses=["w"],
            design_score=5.0,
            animation_potential=5.0,
            summary="one",
        )

    class MarketSummaryLLM:
        def chat_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
            return {
                "market_summary": "Synopsis.",
                "common_strengths": ["cs"],
                "common_weaknesses": ["cw"],
                "differentiation_opportunities": ["diff"],
            }

    app.dependency_overrides[get_llm_client] = lambda: MarketSummaryLLM()  # type: ignore[return-value]
    monkeypatch.setattr("app.services.report_service.parse_page", fake_parse)
    monkeypatch.setattr("app.services.report_service.analyze_competitor_page", fake_analyze)

    response = client_with_openai.post(
        "/reportdemo",
        json={"urls": ["https://bad.example/", "https://good.example/"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["status"] == "failed"
    assert data["items"][0]["reason"] == "timeout"
    assert data["items"][0]["message"]
    assert data["items"][1]["status"] == "ok"
    assert data["items"][1]["analysis"]["title"] == "G"
    assert data["summary"]["market_summary"] == "Synopsis."


def test_analyze_competitor_mocked(
    client_with_openai: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parsed = ParsedPageData(
        requested_url="https://shop.example",
        final_url="https://shop.example/",
        title="Shop",
        meta_description="We sell tools",
        h1="Tools",
        visible_text="Buy quality tools here.",
        screenshot_path=None,
    )

    def fake_parse(u: str, settings: Settings) -> ParsedPageData:
        assert u == "https://shop.example"
        return parsed

    def fake_analyze(llm: Any, data: ParsedPageData) -> CompetitorAnalysisResult:
        assert data.title == "Shop"
        return CompetitorAnalysisResult(
            url=data.requested_url,
            final_url=data.final_url,
            title=data.title,
            positioning="Niche tools seller",
            offer="Quality tools",
            target_audience="DIY",
            strengths=["Clear h1"],
            weaknesses=["Little detail"],
            design_score=6.5,
            animation_potential=7.0,
            summary="Short practical summary.",
        )

    monkeypatch.setattr("app.api.routes.competitors.parse_page", fake_parse)
    monkeypatch.setattr("app.api.routes.competitors.analyze_competitor_page", fake_analyze)

    response = client_with_openai.post(
        "/analyze-competitor",
        json={"url": "https://shop.example", "use_parsing": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert "result" in body
    r = body["result"]
    assert r["positioning"] == "Niche tools seller"
    assert r["offer"] == "Quality tools"
    assert r["target_audience"] == "DIY"
    assert r["design_score"] == 6.5
    assert r["animation_potential"] == 7.0


def test_parsedemo_returns_mocked_result(client_no_llm: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_parse(url: str, settings: Settings) -> ParsedPageData:
        assert url.startswith("http")
        return ParsedPageData(
            requested_url="https://example.com",
            final_url="https://example.com/",
            title="Example",
            meta_description=None,
            h1="Main",
            visible_text="Some visible content here.",
            screenshot_path="data/screenshots/test.png",
        )

    monkeypatch.setattr("app.api.routes.competitors.parse_page", fake_parse)
    response = client_no_llm.post("/parsedemo", json={"url": "https://example.com"})
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    r = data["result"]
    assert r["requested_url"] == "https://example.com"
    assert r["final_url"] == "https://example.com/"
    assert r["title"] == "Example"
    assert r["visible_text"] == "Some visible content here."


def test_filter_competitors_with_llm_parses_indices() -> None:
    candidates = [
        CompetitorCandidate(
            title="A",
            url="https://a.com",
            description="",
            site_type=SiteType.landing,
            source="brave",
        ),
        CompetitorCandidate(
            title="B",
            url="https://b.com",
            description="",
            site_type=SiteType.landing,
            source="brave",
        ),
    ]

    class LLM:
        def chat_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
            return {"selected_indices": [1, 99, 1, 0]}

    out = competitor_filter_service.filter_competitors_with_llm(
        LLM(), "niche", SiteType.landing, "RU", candidates
    )
    assert len(out) == 2
    assert out[0].url == "https://b.com"
    assert out[1].url == "https://a.com"
