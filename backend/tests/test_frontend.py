"""Tests for the SPA mount."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def test_root_returns_stub_when_dist_missing(tmp_path: Path):
    from app.main import create_app

    missing = tmp_path / "does-not-exist"
    with TestClient(create_app(frontend_dist=missing)) as c:
        r = c.get("/")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert "npm run build" in body["message"]


def _make_dist(tmp_path: Path) -> Path:
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text(
        "<html><body><div id='root'></div></body></html>"
    )
    (dist / "assets" / "bundle.js").write_text("console.log('hi')")
    return dist


def test_root_serves_index_html(tmp_path: Path):
    from app.main import create_app

    dist = _make_dist(tmp_path)
    with TestClient(create_app(frontend_dist=dist)) as c:
        r = c.get("/")
        assert r.status_code == 200
        assert "<div id='root'></div>" in r.text
        assert r.headers["content-type"].startswith("text/html")


def test_assets_are_served(tmp_path: Path):
    from app.main import create_app

    dist = _make_dist(tmp_path)
    with TestClient(create_app(frontend_dist=dist)) as c:
        r = c.get("/assets/bundle.js")
        assert r.status_code == 200
        assert "console.log" in r.text


def test_spa_fallback_for_unknown_path(tmp_path: Path):
    from app.main import create_app

    dist = _make_dist(tmp_path)
    with TestClient(create_app(frontend_dist=dist)) as c:
        r = c.get("/some/client/route")
        assert r.status_code == 200
        assert "<div id='root'></div>" in r.text


def test_api_still_works_with_dist_mounted(tmp_path: Path):
    from app.main import create_app

    dist = _make_dist(tmp_path)
    with TestClient(create_app(frontend_dist=dist)) as c:
        r = c.get("/api/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


def test_unknown_api_path_is_404(tmp_path: Path):
    from app.main import create_app

    dist = _make_dist(tmp_path)
    with TestClient(create_app(frontend_dist=dist)) as c:
        r = c.get("/api/nonexistent")
        assert r.status_code == 404
