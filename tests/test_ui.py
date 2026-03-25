"""Smoke tests for the static demo UI."""

from fastapi.testclient import TestClient

from app.main import app


def test_root_returns_html() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert b"AI Competitor Analyzer" in response.content
    assert b"/static/app.js" in response.content


def test_ui_alias() -> None:
    client = TestClient(app)
    r1 = client.get("/")
    r2 = client.get("/ui")
    assert r2.status_code == 200
    assert r1.content == r2.content


def test_static_app_js_returns_200() -> None:
    client = TestClient(app)
    response = client.get("/static/app.js")
    assert response.status_code == 200
    ct = response.headers.get("content-type", "")
    assert "javascript" in ct
    assert b"safeHttpUrl" in response.content
