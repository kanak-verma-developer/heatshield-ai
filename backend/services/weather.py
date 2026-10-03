"""
Real live-weather integration for HeatShield AI.

Uses Open-Meteo (https://open-meteo.com) -- free, no signup, no API key.

DATA HONESTY: if a call fails (no internet, API down) the getters return
None and the caller (services/state.py) falls back to a clearly-flagged DEMO
simulation. Nothing is ever silently faked as real.
"""
import threading
import time

import requests

MORADABAD_LAT = 28.8386
MORADABAD_LON = 78.7733
API_URL = "https://api.open-meteo.com/v1/forecast"
CACHE_SECONDS = 600      # refresh real weather every 10 minutes when it's working
RETRY_SECONDS = 30       # don't hammer the API/network every call when it's down
REQUEST_TIMEOUT = 4      # seconds -- fail fast, never hang the dashboard
MAX_FORECAST_HOURS = 48

_lock = threading.Lock()
_cache = {"data": None, "fetched_at": 0, "last_attempt": 0}


def get_live_weather():
    """Return {'air_temp','humidity','wind_speed','fetched_at','source'} from
    real Open-Meteo data, or None if unreachable. Successful reads are cached
    for CACHE_SECONDS; failures are retried at most every RETRY_SECONDS."""
    now = time.time()
    with _lock:
        if _cache["data"] and (now - _cache["fetched_at"]) < CACHE_SECONDS:
            return _cache["data"]
        if (now - _cache["last_attempt"]) < RETRY_SECONDS and _cache["last_attempt"]:
            # Recently failed (or just refreshed): serve stale data if it is
            # not too old, otherwise report "unreachable".
            if _cache["data"] and (now - _cache["fetched_at"]) < 3 * CACHE_SECONDS:
                return _cache["data"]
            return None
        _cache["last_attempt"] = now
    try:
        resp = requests.get(
            API_URL,
            params={
                "latitude": MORADABAD_LAT,
                "longitude": MORADABAD_LON,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
                "timezone": "Asia/Kolkata",
            },
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        cur = resp.json()["current"]
        data = {
            "air_temp": round(float(cur["temperature_2m"]), 1),
            "humidity": round(float(cur["relative_humidity_2m"]), 1),
            "wind_speed": round(float(cur["wind_speed_10m"]) / 3.6, 2),  # km/h -> m/s
            "fetched_at": now,
            "source": "Open-Meteo (live)",
        }
        with _lock:
            _cache["data"] = data
            _cache["fetched_at"] = now
        return data
    except Exception as exc:  # noqa: BLE001 -- any failure just means "no live data"
        print(f"[weather] live fetch failed, falling back to simulation: {exc}")
        return None


def weather_status():
    """Small helper for the /api/data-sources endpoint."""
    with _lock:
        fresh = _cache["data"] and (time.time() - _cache["fetched_at"]) < 3 * CACHE_SECONDS
        fetched = _cache["fetched_at"]
    if fresh:
        return {"status": "CONNECTED (live)", "last_updated": fetched}
    return {"status": "NOT REACHABLE (using simulation fallback)", "last_updated": None}


_forecast_lock = threading.Lock()
_forecast_cache = {"data": None, "fetched_at": 0, "last_attempt": 0}
FORECAST_CACHE_SECONDS = 1800  # hourly forecast doesn't need refreshing more than every 30 min


def get_weather_forecast(hours_ahead=24):
    """Return a list of {hour_offset, air_temp, humidity, wind_speed} for the
    next `hours_ahead` hours (1..48) from Open-Meteo's real hourly forecast,
    or None if unreachable.

    The cache always holds the FULL 48-hour window and is sliced per request,
    so asking for 6 hours first never truncates a later 24-hour request.
    hour_offset 1 is the hour after the current hour."""
    hours_ahead = max(1, min(MAX_FORECAST_HOURS, int(hours_ahead)))
    now = time.time()
    with _forecast_lock:
        if _forecast_cache["data"] and (now - _forecast_cache["fetched_at"]) < FORECAST_CACHE_SECONDS:
            return _forecast_cache["data"][:hours_ahead]
        if not _forecast_cache["data"] and (now - _forecast_cache["last_attempt"]) < RETRY_SECONDS:
            return None
        _forecast_cache["last_attempt"] = now
    try:
        resp = requests.get(
            API_URL,
            params={
                "latitude": MORADABAD_LAT,
                "longitude": MORADABAD_LON,
                "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
                # index 0 is the current hour; we drop it and keep +1h .. +48h
                "forecast_hours": MAX_FORECAST_HOURS + 1,
                "timezone": "Asia/Kolkata",
            },
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        hourly = resp.json()["hourly"]
        out = []
        for i in range(1, min(len(hourly["time"]), MAX_FORECAST_HOURS + 1)):
            t, h, w = (hourly["temperature_2m"][i], hourly["relative_humidity_2m"][i],
                       hourly["wind_speed_10m"][i])
            if t is None or h is None or w is None:
                break
            out.append({
                "hour_offset": i,
                "air_temp": round(float(t), 1),
                "humidity": round(float(h), 1),
                "wind_speed": round(float(w) / 3.6, 2),
            })
        if not out:
            raise ValueError("empty hourly forecast")
        with _forecast_lock:
            _forecast_cache["data"] = out
            _forecast_cache["fetched_at"] = now
        return out[:hours_ahead]
    except Exception as exc:  # noqa: BLE001
        print(f"[weather] forecast fetch failed, forecast page will use trend fallback: {exc}")
        return None
