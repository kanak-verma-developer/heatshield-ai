"""Tests for the state/weather/history/hotspot logic (no network)."""
import sqlite3
import time

import pytest

import backend.services.weather as weather
from backend.services import db as history_db
from backend.services.state import state, HeatShieldState
from data.zones import ZONES
from ml.hotspot_detection import detect_hotspots
from conftest import fake_open_meteo


def _rows():
    conn = sqlite3.connect(history_db.db_path())
    try:
        return conn.execute("SELECT COUNT(*) FROM risk_readings").fetchone()[0]
    finally:
        conn.close()


def test_snapshot_is_shared_and_cached():
    a = state.get_snapshot()
    b = state.get_snapshot()
    assert a is b


def test_history_is_throttled_to_one_point_per_interval():
    state.get_snapshot()
    base = _rows()
    for _ in range(50):
        state.get_snapshot(max_age=0)           # force recompute every time
    assert _rows() == base                      # ...but no new history rows
    state._last_history_ts = 0                  # pretend the interval elapsed
    state.get_snapshot(max_age=0)
    assert _rows() == base + len(ZONES)


def test_demo_mode_is_deterministic_without_random_noise():
    state._snapshot = None
    a = state.get_snapshot(max_age=0)
    b = state.get_snapshot(max_age=0)
    # two back-to-back computations differ only by the (tiny) simulated-clock advance
    for zid in a:
        assert abs(a[zid]["risk_score"] - b[zid]["risk_score"]) < 0.05


def test_live_weather_is_used_and_flagged(monkeypatch):
    monkeypatch.setattr(weather.requests, "get", lambda url, params=None, timeout=None: fake_open_meteo(url, params))
    snap = state.get_snapshot(max_age=0)
    assert state.data_mode == "LIVE"
    mean_air = sum(f["air_temp"] for f in snap.values()) / len(snap)
    assert 39 < mean_air < 43                   # 41 degC city weather +- urban-heat-island offsets
    assert all(abs(f["wind_speed"] - 2.0) < 0.5 for f in snap.values())   # 7.2 km/h -> 2.0 m/s


def test_forecast_cache_does_not_truncate_later_requests(monkeypatch):
    calls = []
    monkeypatch.setattr(weather.requests, "get",
                        lambda url, params=None, timeout=None: fake_open_meteo(url, params, calls=calls))
    six = weather.get_weather_forecast(6)
    day = weather.get_weather_forecast(24)
    assert len(six) == 6 and len(day) == 24     # regression: second call used to return only 6
    assert len(calls) == 1                      # served from one cached 48 h fetch
    assert six[0]["hour_offset"] == 1 and six[0]["air_temp"] == 31.0   # +1 h = index 1, not the current hour
    assert six[0]["wind_speed"] == 3.0


def test_ml_forecast_uses_live_forecast_when_available(monkeypatch):
    monkeypatch.setattr(weather.requests, "get", lambda url, params=None, timeout=None: fake_open_meteo(url, params))
    fc, method = state.forecast_zone_ml("civil_lines", 12)
    assert method == "live" and len(fc) == 12
    assert fc[-1]["predicted_risk"] > fc[0]["predicted_risk"]   # forecast gets hotter (31 -> 42 degC)


def test_forecast_falls_back_to_trend_when_offline():
    fc, method = state.forecast_zone_ml("civil_lines", 6)
    assert method == "trend_fallback" and len(fc) == 6


def test_city_average_history_only_counts_complete_timestamps():
    state.get_snapshot()
    avg = state.city_average_history()
    assert all(isinstance(t, float) for t, _ in avg)


def test_explanation_is_zone_specific():
    dense = state.explain_zone("moradabad_central")
    green = state.explain_zone("pakwara")
    assert dense["risk_explanation"] != green["risk_explanation"]
    assert dense["drivers"][0]["risk_points_vs_city_avg"] > 0 > green["drivers"][0]["risk_points_vs_city_avg"]


def test_hotspots_flag_citywide_heatwave():
    scores = {z["id"]: 87 + i * 0.3 for i, z in enumerate(ZONES)}
    spots, citywide = detect_hotspots(scores)
    assert citywide is True and len(spots) == len(ZONES)
    assert all(h["severity"] == "EXTREME" for h in spots)


def test_hotspots_flag_single_outlier_but_not_uniform_calm():
    calm = {z["id"]: 30.0 for z in ZONES}
    assert detect_hotspots(calm)[0] == []
    calm[ZONES[0]["id"]] = 65.0
    spots, citywide = detect_hotspots(calm)
    assert [h["zone_id"] for h in spots] == [ZONES[0]["id"]] and not citywide


def test_stale_sklearn_version_only_warns(monkeypatch, tmp_path):
    # metadata says a different version -> warning text is produced, model still loads
    import json, backend.services.state as st
    meta = dict(state.metadata, sklearn_version="0.0.1")
    p = tmp_path / "meta.json"; p.write_text(json.dumps(meta))
    monkeypatch.setattr(st, "META_PATH", str(p))
    fresh = HeatShieldState()
    assert fresh.model is not None and "0.0.1" in (fresh.model_warning or "")
