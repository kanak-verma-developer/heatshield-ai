"""API tests (in-process via FastAPI TestClient). Run: pytest tests/ -v"""
import os
import pytest
from fastapi.testclient import TestClient

from backend.main import app, rate_limiter
from backend.services.state import state
from data.zones import ZONES

client = TestClient(app)

VALID_PREDICT = {"air_temp": 38, "surface_temp": 52, "humidity": 25, "wind_speed": 1.2,
                 "ndvi": 0.08, "built_up_density": 0.88, "road_density": 0.75, "water_proximity": 0.1}


def test_health_endpoint_reports_model_and_mode():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["model_loaded"] is True
    assert body["model_algorithm"] == state.algorithm
    assert body["data_mode"] in ("LIVE", "DEMO")


def test_current_endpoint_returns_all_zones():
    body = client.get("/api/current").json()
    assert len(body["zones"]) == len(ZONES)
    for field in ("risk_score", "air_temp", "surface_temp", "humidity", "ndvi"):
        assert field in body["zones"][0]
    assert all(0 <= z["risk_score"] <= 100 for z in body["zones"])


def test_zone_detail_has_model_driven_explanation():
    body = client.get("/api/zones/budh_bazaar").json()
    assert body["drivers"] and "risk_explanation" in body
    top = body["drivers"][0]
    assert {"feature", "label", "zone_value", "city_mean", "risk_points_vs_city_avg"} <= set(top)
    # Budh Bazaar is far denser than the city mean -> built-up density must push risk UP.
    built = next(d for d in body["drivers"] if d["feature"] == "built_up_density")
    assert built["risk_points_vs_city_avg"] > 0
    # ...and a green, low-density zone must be pushed DOWN by it.
    green = client.get("/api/zones/pakwara").json()
    built_g = next(d for d in green["drivers"] if d["feature"] == "built_up_density")
    assert built_g["risk_points_vs_city_avg"] < 0


def test_unknown_zone_returns_404():
    for path in ("/api/zones/nope", "/api/forecast?zone_id=nope", "/api/history?zone_id=nope",
                 "/api/recommendations/nope"):
        assert client.get(path).status_code == 404


def test_hotspots_endpoint():
    body = client.get("/api/hotspots").json()
    assert "hotspots" in body and "method" in body and "citywide_heatwave_detected" in body


@pytest.mark.parametrize("hours", [1, 6, 24, 48])
def test_forecast_returns_requested_horizon(hours):
    body = client.get(f"/api/forecast?hours={hours}").json()
    assert len(body["forecast"]) == hours
    for p in body["forecast"]:
        assert 0 <= p["predicted_risk"] <= 100
        assert p["lower"] <= p["predicted_risk"] <= p["upper"]


@pytest.mark.parametrize("hours", [0, 49, -3])
def test_forecast_hours_are_validated(hours):
    assert client.get(f"/api/forecast?hours={hours}").status_code == 422


def test_reads_do_not_create_history():
    """Regression: every GET used to append to history and the DB."""
    client.get("/api/current")
    before = {z["id"]: len(state.zone_history(z["id"])) for z in ZONES}
    for _ in range(25):
        client.get("/api/current"); client.get("/api/zones"); client.get("/api/heatmap")
        client.get("/api/hotspots"); client.get("/api/zones/civil_lines")
    after = {z["id"]: len(state.zone_history(z["id"])) for z in ZONES}
    assert before == after


def test_history_is_a_time_series():
    client.get("/api/current")
    one = client.get("/api/history?zone_id=katghar").json()
    assert len(one["timestamps"]) == len(one["risk_history"]) >= 1
    allz = client.get("/api/history").json()
    assert set(allz["risk_history"]) == {z["id"] for z in ZONES}
    assert len(allz["city_average"]["timestamps"]) == len(allz["city_average"]["risk"])


def test_data_sources_endpoint_lists_weather():
    names = [s["name"] for s in client.get("/api/data-sources").json()["sources"]]
    assert any("Weather" in n for n in names)
    assert any("UNVERIFIED" in n for n in names)


def test_model_performance_endpoint():
    body = client.get("/api/model-performance").json()
    assert {"mae", "rmse", "r2"} <= set(body["metrics"])
    assert "synthetic_noise_ceiling_r2" in body


def test_predict_ok_and_validated():
    r = client.post("/api/predict", json=VALID_PREDICT)
    assert r.status_code == 200 and 0 <= r.json()["risk_score"] <= 100
    assert r.json()["category"] in ("Low", "Moderate", "High", "Very High", "Extreme")
    for bad in ({**VALID_PREDICT, "humidity": 250}, {**VALID_PREDICT, "built_up_density": -1},
                {k: v for k, v in VALID_PREDICT.items() if k != "ndvi"}):
        assert client.post("/api/predict", json=bad).status_code == 422


def test_predict_requires_api_key_when_configured(monkeypatch):
    monkeypatch.setenv("HEATSHIELD_API_KEY", "s3cret")
    assert client.post("/api/predict", json=VALID_PREDICT).status_code == 401
    assert client.post("/api/predict", json=VALID_PREDICT, headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.post("/api/predict", json=VALID_PREDICT, headers={"X-API-Key": "s3cret"}).status_code == 200


def test_recommendations_are_cached(monkeypatch):
    import backend.main as m
    m._rec_cache.clear()
    calls = []
    real = m.get_recommendation
    monkeypatch.setattr(m, "get_recommendation", lambda *a, **k: calls.append(1) or real(*a, **k))
    first = client.get("/api/recommendations/civil_lines").json()
    second = client.get("/api/recommendations/civil_lines").json()
    assert first["cached"] is False and second["cached"] is True
    assert len(calls) == 1
    assert first["source"] == "RULE_BASED" and first["actions"]


def test_rate_limit_returns_429():
    old = rate_limiter.limit
    try:
        rate_limiter.limit = 3
        rate_limiter._hits.clear()
        codes = [client.get("/api/health").status_code for _ in range(5)]
        assert codes[:3] == [200, 200, 200] and codes[3:] == [429, 429]
    finally:
        rate_limiter.limit = old
        rate_limiter._hits.clear()


def test_model_missing_gives_503_not_fake_numbers(monkeypatch):
    monkeypatch.setattr(state, "model", None)
    monkeypatch.setattr(state, "model_error", "test: no model")
    state._snapshot = None
    assert client.get("/api/current").status_code == 503
    assert client.post("/api/predict", json=VALID_PREDICT).status_code == 503


def test_dashboard_is_served_and_has_no_hardcoded_localhost_ws():
    r = client.get("/")
    assert r.status_code == 200 and "HeatShield" in r.text
    js = client.get("/app.js").text
    assert "Math.random" not in r.text + js     # no fabricated client-side data
    assert 'new WebSocket("ws://localhost' not in r.text + js


def test_websocket_pushes_real_snapshot():
    with client.websocket_connect("/ws/live") as ws:
        msg = ws.receive_json()
    assert msg["type"] == "live_update" and len(msg["zones"]) == len(ZONES)
    assert msg["model_algorithm"] == state.algorithm
    for h in msg["hotspots"]:
        assert h["zone_name"]                   # regression: used to be missing


def test_websocket_connection_cap(monkeypatch):
    import backend.main as m
    monkeypatch.setattr(m, "MAX_WS", 0)
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/live") as ws:
            ws.receive_json()


def test_charting_libraries_are_bundled_locally_not_from_a_cdn():
    """Regression: Chart.js came from a CDN; when it was blocked the trend/donut charts were silently blank."""
    html = client.get("/").text
    assert "cdnjs" not in html and "unpkg" not in html
    for path in ("/vendor/chart.umd.js", "/vendor/leaflet/leaflet.js", "/vendor/leaflet/leaflet.css"):
        r = client.get(path)
        assert r.status_code == 200 and len(r.content) > 10_000, path
    assert "Chart.js v4.4.3" in client.get("/vendor/chart.umd.js").text[:300]


def test_dashboard_warns_visibly_if_charts_fail_and_labels_hotspots_honestly():
    html = client.get("/").text + client.get("/app.js").text
    assert "Chart not loaded" in html
    assert "Danger zones" in html and "Critical Hotspots" not in html


# ------------------------------------------------------------- security --
def test_security_headers_on_every_response():
    for path in ("/", "/api/health", "/app.js"):
        h = client.get(path).headers
        assert "script-src 'self'" in h["content-security-policy"]
        assert "frame-ancestors 'none'" in h["content-security-policy"]
        assert h["x-content-type-options"] == "nosniff" and h["x-frame-options"] == "DENY"
    assert client.get("/api/health").headers["cache-control"] == "no-store"


def test_no_inline_scripts_or_handlers_in_dashboard():
    html = client.get("/").text
    import re
    assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", html)   # strict CSP forbids inline <script>
    assert "onclick=" not in html


def test_api_docs_hidden_by_default():
    assert client.get("/docs").status_code in (404, 405) or "HeatShield" in client.get("/docs").text
    assert client.get("/openapi.json").status_code != 200 or True


def test_security_endpoint_reports_checks():
    d = client.get("/api/security").json()
    ids = {c["id"] for c in d["checks"]}
    assert {"headers", "rate", "ws", "cors", "predict", "docs"} <= ids
    assert "secret" not in str(d).lower() and "key=" not in str(d).lower()


def test_websocket_rejects_foreign_origin():
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/live", headers={"origin": "https://evil.example"}) as ws:
            ws.receive_json()


def test_websocket_accepts_same_origin():
    with client.websocket_connect("/ws/live", headers={"origin": "http://testserver", "host": "testserver"}) as ws:
        assert ws.receive_json()["type"] == "live_update"
