"""/api/status: the dashboard's honesty labels must reflect reality."""
import pytest
import requests
from fastapi.testclient import TestClient

import backend.main as m
import backend.services.recommendations as rec
import backend.services.weather as weather
from backend.services.state import state
from conftest import fake_open_meteo

client = TestClient(m.app)


def comps():
    body = client.get("/api/status").json()
    return body, {c["id"]: c for c in body["components"]}


def test_demo_mode_is_labelled_demo():
    body, c = comps()
    assert body["data_mode"] == "DEMO" and body["overall"] == "DEMO"
    assert c["weather"]["level"] == "DEMO" and "SIMULATED" in c["weather"]["message"]
    assert c["zone_priors"]["level"] == "ESTIMATE"
    assert c["surface_temp"]["level"] == "ESTIMATE"
    assert c["model"]["level"] == "DEMO" and "SYNTHETIC" in c["model"]["message"]
    assert c["satellite_iot"]["level"] == "MISSING"
    assert c["recommendations"]["level"] == "ESTIMATE"          # no LLM key


def test_live_weather_is_ok_but_overall_stays_demo_because_model_is_synthetic(monkeypatch):
    monkeypatch.setattr(weather.requests, "get", lambda url, params=None, timeout=None: fake_open_meteo(url, params))
    state._snapshot = None
    body, c = comps()
    assert c["weather"]["level"] == "OK" and body["data_mode"] == "LIVE"
    assert body["overall"] == "DEMO"                              # honest: synthetic model + estimated priors


def test_stale_live_weather_is_flagged(monkeypatch):
    monkeypatch.setattr(weather.requests, "get", lambda url, params=None, timeout=None: fake_open_meteo(url, params))
    state._snapshot = None
    client.get("/api/status")
    state.live_weather["fetched_at"] -= 30 * 60
    _, c = comps()
    assert c["weather"]["level"] == "WARN" and "old" in c["weather"]["message"]


def test_missing_model_is_an_error(monkeypatch):
    monkeypatch.setattr(state, "model", None)
    monkeypatch.setattr(state, "model_error", "model file missing")
    state._snapshot = None
    body, c = comps()
    assert c["model"]["level"] == "ERROR" and body["overall"] == "ERROR"


def test_sklearn_version_mismatch_is_a_warning(monkeypatch):
    monkeypatch.setattr(state, "model_warning", "trained with 0.0.1")
    body, c = comps()
    assert c["model"]["level"] == "WARN" and body["overall"] == "WARN"


def test_forecast_status_tracks_how_it_was_made(monkeypatch):
    assert comps()[1]["forecast"]["level"] == "INFO"              # not requested yet
    r = client.get("/api/forecast?hours=3").json()
    assert r["data_quality"] == "ESTIMATE" and comps()[1]["forecast"]["level"] == "ESTIMATE"
    # network "comes back": clear the 30 s retry back-off that the failed call set
    weather._forecast_cache.update({"data": None, "fetched_at": 0, "last_attempt": 0})
    monkeypatch.setattr(weather.requests, "get", lambda url, params=None, timeout=None: fake_open_meteo(url, params))
    r = client.get("/api/forecast?hours=3").json()
    assert r["data_quality"] == "LIVE_FORECAST" and comps()[1]["forecast"]["level"] == "OK"


def test_failed_llm_call_is_a_warning_and_note_is_returned(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "SECRET-KEY")
    m._rec_cache.clear()
    def boom(*a, **k): raise requests.Timeout("slow")
    monkeypatch.setattr(rec.requests, "post", boom)
    out = client.get("/api/recommendations/civil_lines").json()
    assert out["source"] == "RULE_BASED" and "failed" in out["note"]
    c = comps()[1]["recommendations"]
    assert c["level"] == "WARN" and "Timeout" in c["message"] and "SECRET-KEY" not in c["message"]


def test_successful_llm_call_is_ok(monkeypatch):
    import json
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    m._rec_cache.clear()
    class R:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return {"candidates": [{"content": {"parts": [{"text": json.dumps({"priority": "LOW", "actions": ["x"]})}]}}]}
    monkeypatch.setattr(rec.requests, "post", lambda *a, **k: R())
    client.get("/api/recommendations/civil_lines")
    c = comps()[1]["recommendations"]
    assert c["level"] == "OK" and "gemini" in c["message"]


def test_history_info_then_ok():
    state.get_snapshot()
    _, c = comps()
    assert c["history"]["level"] in ("INFO", "OK")


def test_dashboard_contains_the_labelling_hooks():
    html = client.get("/").text + client.get("/app.js").text
    for hook in ("statusList", "overallChip", "badgeMap", "badgeRecs", "badgeModel", "badgeForecast",
                 "staleBadge", "loadError("):
        assert hook in html
