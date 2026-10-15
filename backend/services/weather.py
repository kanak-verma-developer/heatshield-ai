"""
Real live-weather integration for HeatShield AI.

Uses Open-Meteo (https://open-meteo.com) -- free, no signup, no API key.

DATA HONESTY: if a call fails (no internet, API down) the getters return
None and the caller (services/state.py) decides what to do. For Moradabad
it falls back to a clearly-flagged DEMO simulation; for other cities it
reports "unavailable". Nothing is ever silently faked as real.

Note: Open-Meteo weather comes from a model grid (a few km wide). Two zones
very close to each other can therefore get identical readings. Zones in
different parts of a big city (like Delhi) will differ.
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
        out = _parse_hourly(resp.json()["hourly"])
        if not out:
            raise ValueError("empty hourly forecast")
        with _forecast_lock:
            _forecast_cache["data"] = out
            _forecast_cache["fetched_at"] = now
        return out[:hours_ahead]
    except Exception as exc:  # noqa: BLE001
        print(f"[weather] forecast fetch failed, forecast page will use trend fallback: {exc}")
        return None


def _parse_hourly(hourly):
    """Open-Meteo 'hourly' block -> [{hour_offset, air_temp, humidity, wind_speed(m/s)}]."""
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
    return out


# ------------------------------------------------------------ city weather --
_city_lock = threading.Lock()
_city_cache = {}  # city -> {"data": {...}, "fetched_at": ts}

CITY_COORDS = {
    "Moradabad": (28.8386, 78.7733),
    "Delhi": (28.6139, 77.2090),
}


def get_city_weather(city):
    """Live weather for a supported city from Open-Meteo, or None if unreachable."""
    if city not in CITY_COORDS:
        return None
    now = time.time()
    with _city_lock:
        cached = _city_cache.get(city)
        if cached and (now - cached["fetched_at"]) < CACHE_SECONDS:
            return cached["data"]
    lat, lon = CITY_COORDS[city]
    try:
        resp = requests.get(
            API_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
                "timezone": "Asia/Kolkata",
            },
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        cur = resp.json()["current"]
        data = {
            "city": city,
            "temperature": round(float(cur["temperature_2m"]), 1),
            "humidity": round(float(cur["relative_humidity_2m"])),
            "wind_speed_kmh": round(float(cur["wind_speed_10m"]), 1),
            "updated_at": cur.get("time"),
            "source": "Open-Meteo (live)",
        }
        with _city_lock:
            _city_cache[city] = {"data": data, "fetched_at": now}
        return data
    except Exception as exc:  # noqa: BLE001
        print(f"[weather] {city} live fetch failed: {exc}")
        with _city_lock:
            cached = _city_cache.get(city)
            if cached and (now - cached["fetched_at"]) < 3 * CACHE_SECONDS:
                return cached["data"]
        return None


# ------------------------------------------------- per-zone weather (batch) --
_zones_lock = threading.Lock()
_zones_cache = {}  # tuple(zone ids) -> {"data", "fetched_at", "last_attempt"}


def get_zones_weather(zones):
    """Real current weather for EVERY zone's own coordinates, in ONE request.

    `zones` is a list of zone dicts (id, lat, lon). Returns
    {zone_id: {"air_temp", "humidity", "wind_speed" (m/s), "updated_at"}}
    or None if unreachable. Cached for CACHE_SECONDS; failures are retried at
    most every RETRY_SECONDS; stale data is served for up to 3x the cache time."""
    if not zones:
        return None
    key = tuple(z["id"] for z in zones)
    now = time.time()
    with _zones_lock:
        entry = _zones_cache.get(key)
        if entry and entry["data"] and (now - entry["fetched_at"]) < CACHE_SECONDS:
            return entry["data"]
        if entry and entry["last_attempt"] and (now - entry["last_attempt"]) < RETRY_SECONDS:
            if entry["data"] and (now - entry["fetched_at"]) < 3 * CACHE_SECONDS:
                return entry["data"]
            return None
        if entry is None:
            entry = _zones_cache[key] = {"data": None, "fetched_at": 0, "last_attempt": 0}
        entry["last_attempt"] = now
    try:
        resp = requests.get(
            API_URL,
            params={
                "latitude": ",".join(str(z["lat"]) for z in zones),
                "longitude": ",".join(str(z["lon"]) for z in zones),
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
                "timezone": "Asia/Kolkata",
            },
            timeout=REQUEST_TIMEOUT + 4,     # many locations: allow a little longer
        )
        resp.raise_for_status()
        payload = resp.json()
        items = payload if isinstance(payload, list) else [payload]   # 1 zone -> dict
        if len(items) != len(zones):
            raise ValueError(f"expected {len(zones)} locations, got {len(items)}")
        data = {}
        for z, item in zip(zones, items):
            cur = item["current"]
            data[z["id"]] = {
                "air_temp": round(float(cur["temperature_2m"]), 1),
                "humidity": round(float(cur["relative_humidity_2m"]), 1),
                "wind_speed": round(float(cur["wind_speed_10m"]) / 3.6, 2),  # km/h -> m/s
                "updated_at": cur.get("time"),
            }
        with _zones_lock:
            entry["data"] = data
            entry["fetched_at"] = now
        return data
    except Exception as exc:  # noqa: BLE001
        print(f"[weather] per-zone batch fetch failed: {exc}")
        return None


# ------------------------------------------------ forecast for any location --
_loc_forecast_lock = threading.Lock()
_loc_forecast_cache = {}  # (lat, lon) -> {"data", "fetched_at", "last_attempt"}


def get_location_forecast(lat, lon, hours_ahead=24):
    """Same output as get_weather_forecast(), but for any coordinates (used
    for Delhi zones). Returns None if unreachable."""
    hours_ahead = max(1, min(MAX_FORECAST_HOURS, int(hours_ahead)))
    key = (round(float(lat), 3), round(float(lon), 3))
    now = time.time()
    with _loc_forecast_lock:
        entry = _loc_forecast_cache.get(key)
        if entry and entry["data"] and (now - entry["fetched_at"]) < FORECAST_CACHE_SECONDS:
            return entry["data"][:hours_ahead]
        if entry and not entry["data"] and (now - entry["last_attempt"]) < RETRY_SECONDS:
            return None
        if entry is None:
            entry = _loc_forecast_cache[key] = {"data": None, "fetched_at": 0, "last_attempt": 0}
        entry["last_attempt"] = now
    try:
        resp = requests.get(
            API_URL,
            params={
                "latitude": key[0],
                "longitude": key[1],
                "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
                "forecast_hours": MAX_FORECAST_HOURS + 1,
                "timezone": "Asia/Kolkata",
            },
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        out = _parse_hourly(resp.json()["hourly"])
        if not out:
            raise ValueError("empty hourly forecast")
        with _loc_forecast_lock:
            entry["data"] = out
            entry["fetched_at"] = now
        return out[:hours_ahead]
    except Exception as exc:  # noqa: BLE001
        print(f"[weather] location forecast failed for {key}: {exc}")
        return None


def city_weather_status(city):
    """For /api/data-sources: is live weather for this city currently cached?"""
    with _city_lock:
        cached = _city_cache.get(city)
    if cached and (time.time() - cached["fetched_at"]) < 3 * CACHE_SECONDS:
        return {"status": "CONNECTED (live)", "last_updated": cached["fetched_at"]}
    return {"status": "NOT REACHABLE", "last_updated": None}


# =====================================================================
# SIMPLE PUBLIC VIEW  (added: plain numbers for everyday users)
# Real weather only. "Feels like" = NOAA heat index (temperature + humidity).
# =====================================================================
import math
from datetime import datetime, timedelta, timezone

_IST = timezone(timedelta(hours=5, minutes=30))


def heat_index_c(temp_c, rh):
    """NOAA / Rothfusz heat index, in degrees C."""
    t = temp_c * 9.0 / 5.0 + 32.0
    simple = 0.5 * (t + 61.0 + (t - 68.0) * 1.2 + rh * 0.094)
    if (simple + t) / 2.0 < 80.0:
        hi = simple
    else:
        hi = (-42.379 + 2.04901523 * t + 10.14333127 * rh
              - 0.22475541 * t * rh - 0.00683783 * t * t
              - 0.05481717 * rh * rh + 0.00122874 * t * t * rh
              + 0.00085282 * t * rh * rh - 0.00000199 * t * t * rh * rh)
        if rh < 13 and 80 <= t <= 112:
            hi -= ((13 - rh) / 4.0) * math.sqrt((17 - abs(t - 95.0)) / 17.0)
        elif rh > 85 and 80 <= t <= 87:
            hi += ((rh - 85) / 10.0) * ((87 - t) / 5.0)
    return (hi - 32.0) * 5.0 / 9.0


def feels_like_c(temp_c, rh):
    """Never lower than the real air temperature (safer for heat warnings)."""
    return round(max(temp_c, heat_index_c(temp_c, rh)), 1)


def heat_level(feels_c):
    """NOAA heat-index bands, converted to degrees C."""
    if feels_c < 26.7:
        return "safe"
    if feels_c < 32.2:
        return "caution"
    if feels_c < 39.4:
        return "extreme_caution"
    if feels_c < 51.1:
        return "danger"
    return "extreme_danger"


def _simple_row(temp, rh, wind_kmh):
    fl = feels_like_c(temp, rh)
    return {"temp": round(temp, 1), "feels_like": fl, "humidity": round(rh),
            "wind_kmh": round(wind_kmh, 1), "level": heat_level(fl)}


def get_simple_city(city, zones):
    """Plain, real-weather-only summary for one city, or None if the live
    weather cannot be fetched."""
    zw = get_zones_weather(zones)
    if not zw:
        return None
    rows = []
    for z in zones:
        w = zw.get(z["id"])
        if not w:
            continue
        row = _simple_row(w["air_temp"], w["humidity"], w["wind_speed"] * 3.6)
        row.update({"id": z["id"], "name": z["name"], "lat": z["lat"], "lon": z["lon"]})
        rows.append(row)
    if not rows:
        return None
    n = len(rows)
    city_now = _simple_row(sum(r["temp"] for r in rows) / n,
                           sum(r["humidity"] for r in rows) / n,
                           sum(r["wind_kmh"] for r in rows) / n)
    _apply_zone_adjustment(rows, zones)
    stamps = [w.get("updated_at") for w in zw.values() if w.get("updated_at")]

    forecast = []
    lat, lon = CITY_COORDS.get(city, (zones[0]["lat"], zones[0]["lon"]))
    wf = get_location_forecast(lat, lon, 6)
    if wf:
        base = datetime.now(_IST).replace(minute=0, second=0, microsecond=0)
        for p in wf:
            fl = feels_like_c(p["air_temp"], p["humidity"])
            when = base + timedelta(hours=p["hour_offset"])
            forecast.append({"label": when.strftime("%I %p").lstrip("0"),
                             "temp": p["air_temp"], "feels_like": fl,
                             "level": heat_level(fl)})
    try:
        extras = get_city_extras(city, lat, lon)
    except Exception:  # noqa: BLE001
        extras = None
    return {"city": city, "updated_at": max(stamps) if stamps else None,
            "city_now": city_now, "zones": rows, "forecast": forecast, "extras": extras,
            **_hottest_coolest(rows)}

_extras_lock = threading.Lock()
_extras_cache = {}
AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def get_city_extras(city, lat, lon):
    """Day chart (24h feels-like, UV, rain chance), sunrise/sunset and air
    quality for a city. Every part is optional: failures just leave it empty."""
    now = time.time()
    with _extras_lock:
        c = _extras_cache.get(city)
        if c and now - c["t"] < 900:
            return c["d"]
    out = {"now_hour": datetime.now(_IST).hour, "hourly": [], "sunrise": None,
           "sunset": None, "uv_max": None, "aqi": None}
    ok = False
    try:
        r = requests.get(API_URL, params={
            "latitude": lat, "longitude": lon,
            "hourly": "temperature_2m,relative_humidity_2m,uv_index,precipitation_probability",
            "daily": "sunrise,sunset,uv_index_max", "forecast_days": 1,
            "timezone": "Asia/Kolkata"}, timeout=REQUEST_TIMEOUT + 3)
        r.raise_for_status()
        j = r.json()
        h = j["hourly"]
        for i, tm in enumerate(h["time"]):
            t, rh = h["temperature_2m"][i], h["relative_humidity_2m"][i]
            if t is None or rh is None:
                continue
            fl = feels_like_c(t, rh)
            uv, rain = h["uv_index"][i], h["precipitation_probability"][i]
            out["hourly"].append({"hour": int(tm[11:13]), "temp": round(t, 1), "feels_like": fl,
                                  "level": heat_level(fl), "uv": None if uv is None else round(uv, 1),
                                  "rain": rain})
        d = j.get("daily") or {}
        out["sunrise"] = (d.get("sunrise") or [None])[0]
        out["sunset"] = (d.get("sunset") or [None])[0]
        out["uv_max"] = (d.get("uv_index_max") or [None])[0]
        ok = bool(out["hourly"])
    except Exception as exc:  # noqa: BLE001
        print(f"[weather] day extras failed for {city}: {exc}")
    try:
        r = requests.get(AQ_URL, params={"latitude": lat, "longitude": lon,
                                         "current": "us_aqi,pm2_5", "timezone": "Asia/Kolkata"},
                         timeout=REQUEST_TIMEOUT + 3)
        r.raise_for_status()
        cur = r.json()["current"]
        if cur.get("us_aqi") is not None:
            out["aqi"] = {"us_aqi": round(cur["us_aqi"]), "pm25": cur.get("pm2_5")}
            ok = True
    except Exception as exc:  # noqa: BLE001
        print(f"[weather] air quality failed for {city}: {exc}")
    with _extras_lock:
        _extras_cache[city] = {"d": out, "t": now if ok else now - 600}   # retry failures after ~5 min
    return out


# =====================================================================
# ZONE-WISE ADJUSTMENT  (ESTIMATED, NOT MEASURED)
# Open-Meteo gives one reading per model grid cell, so nearby zones come back
# identical. To show how zones differ inside a city we add a small urban-heat
# offset worked out from the land-cover priors in data/zones.py (built-up
# density, tree cover, road density, water). Those priors are hand-set and
# unverified, so every adjusted row is marked estimated=True and keeps the raw
# value in temp_grid. Offsets are centred on the city mean, so the city-wide
# average stays equal to the real reading.
# =====================================================================
ZONE_ADJ_SCALE = 6.0    # degrees C per unit of score difference
ZONE_ADJ_CAP = 2.5      # never adjust a zone by more than +/- this many degrees C


def _zone_score(z):
    return (0.50 * z["built_up_density"] + 0.25 * z["road_density"]
            - 0.35 * z["ndvi_base"] - 0.15 * z["water_proximity"])


_HOT_REASONS = [
    (lambda z: z["built_up_density"] >= 0.80, "dense buildings", "घनी इमारतें"),
    (lambda z: z["road_density"] >= 0.70, "heavy traffic and tar roads", "भारी ट्रैफिक और पक्की सड़कें"),
    (lambda z: z["ndvi_base"] <= 0.15, "very few trees", "पेड़ बहुत कम"),
]
_COOL_REASONS = [
    (lambda z: z["built_up_density"] <= 0.45, "more open space", "खुली जगह ज़्यादा"),
    (lambda z: z["ndvi_base"] >= 0.35, "more trees and greenery", "पेड़ और हरियाली ज़्यादा"),
    (lambda z: z["water_proximity"] >= 0.40, "close to water", "पानी के पास"),
]


def _zone_why(z, adj):
    """One short line (English, Hindi) on why this zone is warmer or cooler."""
    if adj >= 0.5:
        reasons = [(e, h) for ok, e, h in _HOT_REASONS if ok(z)]
        if not reasons:
            reasons = [("more built-up land and less greenery", "ज़्यादा पक्का इलाका और कम हरियाली")]
        return ("Warmer than the city average: " + ", ".join(e for e, _ in reasons) + ".",
                "शहर के औसत से ज़्यादा गर्म: " + ", ".join(h for _, h in reasons) + "।")
    if adj <= -0.5:
        reasons = [(e, h) for ok, e, h in _COOL_REASONS if ok(z)]
        if not reasons:
            reasons = [("less built-up land", "कम पक्का इलाका")]
        return ("Cooler than the city average: " + ", ".join(e for e, _ in reasons) + ".",
                "शहर के औसत से ठंडा: " + ", ".join(h for _, h in reasons) + "।")
    return ("Close to the city average.", "शहर के औसत के आसपास।")


def _zone_advice(level, adj):
    """Zone-specific advice (English, Hindi). (None, None) when it is safe."""
    if level == "safe":
        return None, None
    if level == "caution":
        en = "Avoid long outdoor work here from 12 pm to 4 pm. Drink water often."
        hi = "यहाँ दोपहर 12 से 4 बजे तक लंबे समय बाहर काम न करें। बार-बार पानी पिएँ।"
    else:
        en = "Avoid going out here from 12 pm to 4 pm. Drink water often and rest in shade."
        hi = "यहाँ दोपहर 12 से 4 बजे तक बाहर न निकलें। बार-बार पानी पिएँ और छाया में आराम करें।"
    if adj >= 1.0:
        en += " Narrow crowded lanes hold heat, so choose shaded or open spots."
        hi += " तंग और भीड़ वाली गलियाँ गर्मी रोक लेती हैं, छायादार या खुली जगह चुनें।"
    return en, hi


def _apply_zone_adjustment(rows, zones):
    """Adds the estimated zone offset to each row, in place."""
    by_id = {z["id"]: z for z in zones}
    scores = {r["id"]: _zone_score(by_id[r["id"]]) for r in rows if r["id"] in by_id}
    if not scores:
        return
    mean = sum(scores.values()) / len(scores)
    for r in rows:
        z = by_id.get(r["id"])
        if not z:
            continue
        adj = (scores[r["id"]] - mean) * ZONE_ADJ_SCALE
        adj = round(max(-ZONE_ADJ_CAP, min(ZONE_ADJ_CAP, adj)), 1)
        grid_temp = r["temp"]
        r.update(_simple_row(round(grid_temp + adj, 1), r["humidity"], r["wind_kmh"]))
        why_en, why_hi = _zone_why(z, adj)
        adv_en, adv_hi = _zone_advice(r["level"], adj)
        r.update({"temp_grid": grid_temp, "adj": adj, "estimated": True,
                  "why": why_en, "why_hi": why_hi, "advice": adv_en, "advice_hi": adv_hi})


def _hottest_coolest(rows):
    def pick(r):
        return {"id": r["id"], "name": r["name"], "temp": r["temp"],
                "feels_like": r["feels_like"], "level": r["level"]}
    return {"hottest": pick(max(rows, key=lambda r: r["feels_like"])),
            "coolest": pick(min(rows, key=lambda r: r["feels_like"]))}

