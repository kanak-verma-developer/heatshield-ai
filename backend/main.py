"""
HeatShield AI backend - FastAPI application.

Run (from the project root):   uvicorn backend.main:app --port 8000
or, from inside backend/:      uvicorn main:app --port 8000
Dashboard:                     http://localhost:8000/        (served by this app)
Swagger docs:                  http://localhost:8000/docs

Environment variables (all optional, see .env.example):
  ALLOWED_ORIGINS               comma-separated CORS origins
  HEATSHIELD_RATE_LIMIT_PER_MIN per-IP limit for /api/* (default 240, 0 = off)
  HEATSHIELD_MAX_WS             max simultaneous WebSocket clients (default 50)
  HEATSHIELD_API_KEY            if set, POST /api/predict requires X-API-Key
  HEATSHIELD_REC_TTL            recommendation cache seconds (default 600)
  GEMINI_API_KEY                enables Gemini-generated recommendations (GEMINI_MODEL optional)
  ANTHROPIC_API_KEY             enables Claude-generated recommendations instead
  HEATSHIELD_LLM_PROVIDER       gemini | claude | none (only needed if both keys are set)
"""
import asyncio
import os
import secrets
import sys
import threading
import time
from collections import defaultdict, deque

from fastapi import FastAPI, Header, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from data.zones import ZONES, ZONE_BY_ID
from ml.hotspot_detection import detect_hotspots
from backend.services.state import state, ModelNotAvailable, FEATURES
from backend.services.recommendations import get_recommendation, active_provider, llm_status
from backend.services.weather import weather_status

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


def _load_dotenv(path):
    """Minimal .env loader (KEY=VALUE lines). Real environment variables win."""
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k and v and k not in os.environ:
                    os.environ[k] = v
    except FileNotFoundError:
        pass


_load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Interactive API docs are off by default (they list every endpoint to strangers).
# Set HEATSHIELD_ENABLE_DOCS=1 while developing.
_DOCS_ON = os.environ.get("HEATSHIELD_ENABLE_DOCS") == "1"
app = FastAPI(title="HeatShield AI API", version="1.3.0",
              description="Urban Heat Intelligence Platform for Moradabad, UP, India",
              docs_url="/docs" if _DOCS_ON else None, redoc_url=None,
              openapi_url="/openapi.json" if _DOCS_ON else None)

_default_origins = "http://localhost:8000,http://127.0.0.1:8000"   # file:// ("null") no longer allowed by default
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", _default_origins).split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)

START_TIME = time.time()


# ------------------------------------------------------------ rate limit --
class RateLimiter:
    """Tiny in-memory sliding-window limiter (per client IP, per process).
    Behind a reverse proxy every request shares the proxy's IP -- use the
    proxy's own rate limiting in that case."""

    def __init__(self, limit_per_min: int):
        self.limit = limit_per_min
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        if self.limit <= 0:
            return True
        now = time.monotonic()
        with self._lock:
            if len(self._hits) > 10000:
                self._hits = defaultdict(deque, {k: v for k, v in self._hits.items()
                                                 if v and now - v[-1] < 60})
            q = self._hits[key]
            while q and now - q[0] > 60:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True


rate_limiter = RateLimiter(int(os.environ.get("HEATSHIELD_RATE_LIMIT_PER_MIN", 240)))


@app.middleware("http")
async def _rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        client = request.client.host if request.client else "unknown"
        if not rate_limiter.allow(client):
            return JSONResponse({"detail": "rate limit exceeded, slow down"}, status_code=429,
                                headers={"Retry-After": "30"})
    return await call_next(request)


# ------------------------------------------------------- security headers --
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
       "img-src 'self' data: https://*.tile.openstreetmap.org; media-src 'self'; "
       "font-src 'self' data:; connect-src 'self' ws: wss:; object-src 'none'; "
       "base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
SECURITY_HEADERS = {
    "Content-Security-Policy": CSP,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=(), payment=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}


@app.middleware("http")
async def _security_headers(request: Request, call_next):
    resp = await call_next(request)
    for k, v in SECURITY_HEADERS.items():
        resp.headers.setdefault(k, v)
    if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
        resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if request.url.path.startswith("/api/"):
        resp.headers.setdefault("Cache-Control", "no-store")
    return resp


@app.get("/api/security")
def security_overview():
    """Honest, non-sensitive summary shown in the dashboard's Security panel."""
    key = bool(os.environ.get("HEATSHIELD_API_KEY"))
    return {"checks": [
        {"id": "headers", "label": "Browser protection headers", "ok": True,
         "detail": "CSP, no-sniff, anti-framing and referrer rules are sent on every response."},
        {"id": "rate", "label": "Request rate limit", "ok": rate_limiter.limit > 0,
         "detail": f"{rate_limiter.limit} API requests per minute per visitor." if rate_limiter.limit > 0 else "Disabled."},
        {"id": "ws", "label": "Live-feed origin check", "ok": True,
         "detail": f"Live feed accepts only trusted sites, max {MAX_WS_PER_IP} connections per visitor."},
        {"id": "cors", "label": "Cross-site access", "ok": "null" not in ALLOWED_ORIGINS and "*" not in ALLOWED_ORIGINS,
         "detail": f"{len(ALLOWED_ORIGINS)} trusted origin(s) allowed."},
        {"id": "predict", "label": "Prediction endpoint key", "ok": key,
         "detail": "Protected by an API key." if key else "Open. Set HEATSHIELD_API_KEY to lock it."},
        {"id": "docs", "label": "API docs hidden", "ok": not _DOCS_ON,
         "detail": "Hidden from the public." if not _DOCS_ON else "Visible (development mode)."},
    ]}


@app.exception_handler(ModelNotAvailable)
async def _model_unavailable(_request, exc):
    return JSONResponse({"detail": f"model not available: {exc}"}, status_code=503)


def _zone_public(zone_id, feats):
    zone = ZONE_BY_ID[zone_id]
    return {"zone_id": zone_id, "zone_name": zone["name"], "lat": zone["lat"], "lon": zone["lon"], **feats}


def _require_zone(zone_id):
    if zone_id not in ZONE_BY_ID:
        raise HTTPException(404, "zone not found")


# ---------------------------------------------------------------- health ---
@app.get("/api/health")
def health():
    snap_ok = True
    if state.model_ready():
        state.get_snapshot()          # refreshes data_mode; cached, cheap
    else:
        snap_ok = False
    return {
        "status": "ok" if snap_ok else "degraded",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "model_loaded": state.model_ready(),
        "model_algorithm": state.algorithm,
        "model_error": state.model_error,
        "model_warning": state.model_warning,
        "data_mode": state.data_mode,
    }


# --------------------------------------------------------------- current ---
@app.get("/api/current")
def current():
    snapshot = state.get_snapshot()
    zones_out = [_zone_public(zid, f) for zid, f in snapshot.items()]
    n = len(zones_out)
    hotspots, citywide = detect_hotspots({zid: f["risk_score"] for zid, f in snapshot.items()})
    return {
        "data_mode": state.data_mode,
        "timestamp": time.time(),
        "model_algorithm": state.algorithm,
        "avg_air_temp": round(sum(z["air_temp"] for z in zones_out) / n, 1),
        "avg_heat_risk": round(sum(z["risk_score"] for z in zones_out) / n, 1),
        "critical_hotspots": len(hotspots),
        "citywide_heatwave_detected": citywide,
        "max_surface_temp": round(max(z["surface_temp"] for z in zones_out), 1),
        "avg_ndvi": round(sum(z["ndvi"] for z in zones_out) / n, 3),
        "zones": zones_out,
    }


# ----------------------------------------------------------------- zones ---
@app.get("/api/zones")
def zones():
    snapshot = state.get_snapshot()
    return {"data_mode": state.data_mode,
            "zones": [_zone_public(zid, f) for zid, f in snapshot.items()]}


@app.get("/api/zones/{zone_id}")
def zone_detail(zone_id: str):
    _require_zone(zone_id)
    feats = state.zone_snapshot(zone_id)
    explanation = state.explain_zone(zone_id)
    return {
        "data_mode": state.data_mode,
        **_zone_public(zone_id, feats),
        "feature_importance": state.feature_importance_pct(),
        "feature_importance_method": state.metadata.get("importance_method"),
        **explanation,
    }


# --------------------------------------------------------------- heatmap ---
@app.get("/api/heatmap")
def heatmap():
    snapshot = state.get_snapshot()
    return {
        "data_mode": state.data_mode,
        "points": [{"zone_id": zid, "lat": ZONE_BY_ID[zid]["lat"], "lon": ZONE_BY_ID[zid]["lon"],
                    "risk_score": f["risk_score"]} for zid, f in snapshot.items()],
    }


# -------------------------------------------------------------- hotspots ---
@app.get("/api/hotspots")
def hotspots():
    snapshot = state.get_snapshot()
    scores = {zid: f["risk_score"] for zid, f in snapshot.items()}
    spots, citywide_event = detect_hotspots(scores)
    out = [{**h, "zone_name": ZONE_BY_ID[h["zone_id"]]["name"], "detected_at": time.time()} for h in spots]
    return {
        "data_mode": state.data_mode,
        "method": ("z-score anomaly detection (relative outlier, threshold=1.5σ) OR absolute risk >= 71 "
                   "(catches city-wide heatwaves that z-score alone would miss). Because zone land-cover "
                   "values are fixed priors, the same dense zones will usually rank highest."),
        "citywide_heatwave_detected": citywide_event,
        "hotspots": out,
    }


# -------------------------------------------------------------- forecast ---
@app.get("/api/forecast")
def forecast(zone_id: str = None, hours: int = Query(6, ge=1, le=48)):
    if zone_id is None:
        zone_id = ZONES[0]["id"]
    _require_zone(zone_id)
    fc, method = state.forecast_zone_ml(zone_id, hours_ahead=hours)
    return {
        "data_mode": state.data_mode,
        "zone_id": zone_id,
        "zone_name": ZONE_BY_ID[zone_id]["name"],
        "method": ("Real Open-Meteo hourly forecast run through the trained ML model"
                   if method == "live" else
                   "Trend + diurnal extrapolation over recent model outputs (live forecast weather unreachable)"),
        "data_quality": "LIVE_FORECAST" if method == "live" else "ESTIMATE",
        "forecast": fc,
    }


# ----------------------------------------------------------------- status --
_SEVERITY = {"ERROR": 4, "WARN": 3, "DEMO": 2, "ESTIMATE": 1, "OK": 0, "INFO": 0, "MISSING": 0}


@app.get("/api/status")
def status():
    """Plain-language truth about every part of the system, for the dashboard's
    status panel and inline badges. Levels: OK (real/working), DEMO (simulated),
    ESTIMATE (assumption/approximation), WARN (degraded, check it), ERROR
    (broken), MISSING (not connected), INFO (just so you know)."""
    comps = []

    def add(cid, label, level, message):
        comps.append({"id": cid, "label": label, "level": level, "message": message})

    if state.model_ready():
        state.get_snapshot()          # refresh data_mode; cached and cheap

    # Weather
    if state.data_mode == "LIVE":
        age_min = (time.time() - state.live_weather["fetched_at"]) / 60
        if age_min > 20:
            add("weather", "Weather", "WARN", f"Real Open-Meteo data but {age_min:.0f} min old (refresh failing?)")
        else:
            add("weather", "Weather", "OK", "Real current weather from Open-Meteo")
    else:
        add("weather", "Weather", "DEMO", "Open-Meteo not reachable: temperature/humidity/wind are SIMULATED")

    # Zone land-cover priors / surface temp
    add("zone_priors", "Zone land-cover", "ESTIMATE",
        "Built-up, vegetation, roads, water are hand-set unverified values, not measured. "
        "Zone ranking and hotspots mostly come from these.")
    add("surface_temp", "Surface temperature", "ESTIMATE",
        "Computed from air temp + the estimates above, not a satellite measurement")

    # Model
    if not state.model_ready():
        add("model", "ML model", "ERROR", f"Model not loaded: {state.model_error}. Predictions are unavailable.")
    elif state.model_warning:
        add("model", "ML model", "WARN", state.model_warning)
    else:
        r2 = state.metadata.get("metrics", {}).get("r2")
        add("model", "ML model", "DEMO",
            f"{state.algorithm} trained on SYNTHETIC data (R² {r2} only shows it learned the synthetic formula, "
            f"not real-world accuracy)")

    # Forecast
    if state.last_forecast_method == "live":
        add("forecast", "Forecast", "OK", "Model run on Open-Meteo's real hourly forecast")
    elif state.last_forecast_method == "trend_fallback":
        add("forecast", "Forecast", "ESTIMATE", "Live forecast unreachable: using a simple trend extrapolation")
    else:
        add("forecast", "Forecast", "INFO", "Not requested yet (open the Forecast page)")

    # Recommendations
    provider, llm = active_provider(), llm_status()
    if provider is None:
        add("recommendations", "Recommendations", "ESTIMATE",
            "Rule-based advice (no GEMINI_API_KEY / ANTHROPIC_API_KEY set)")
    elif llm["last_ok"] is False:
        add("recommendations", "Recommendations", "WARN",
            f"{provider} call failed ({llm['last_error']}): showing rule-based fallback")
    elif llm["last_ok"] is True:
        add("recommendations", "Recommendations", "OK", f"Written by {provider}")
    else:
        add("recommendations", "Recommendations", "INFO", f"{provider} configured, not used yet")

    # History
    n = len(state.zone_history(ZONES[0]["id"])) if state.model_ready() else 0
    add("history", "History / trend", "INFO" if n < 3 else "OK",
        f"{n} stored point(s), 1 per {os.environ.get('HEATSHIELD_HISTORY_INTERVAL', '60')} s"
        + (" - trend chart fills up over time" if n < 3 else ""))

    add("satellite_iot", "Satellite / IoT sensors", "MISSING", "Not connected: no real land-surface data yet")

    overall = max((c["level"] for c in comps if c["level"] in ("ERROR", "WARN", "DEMO")),
                  key=lambda l: _SEVERITY[l], default="OK")
    return {"data_mode": state.data_mode, "overall": overall, "components": comps}


# ---------------------------------------------------------------- history --
@app.get("/api/history")
def history(zone_id: str = None):
    interval = float(os.environ.get("HEATSHIELD_HISTORY_INTERVAL", 60))
    state.get_snapshot()
    if zone_id:
        _require_zone(zone_id)
        h = state.zone_history(zone_id)
        return {"data_mode": state.data_mode, "zone_id": zone_id, "interval_seconds": interval,
                "timestamps": [t for t, _ in h], "risk_history": [s for _, s in h]}
    avg = state.city_average_history()
    return {
        "data_mode": state.data_mode,
        "interval_seconds": interval,
        "risk_history": {zid: [s for _, s in state.zone_history(zid)] for zid in ZONE_BY_ID},
        "timestamps": {zid: [t for t, _ in state.zone_history(zid)] for zid in ZONE_BY_ID},
        "city_average": {"timestamps": [t for t, _ in avg], "risk": [r for _, r in avg]},
    }


# ---------------------------------------------------------- data sources ---
@app.get("/api/data-sources")
def data_sources():
    provider = active_provider()
    w_status = weather_status()
    return {
        "data_mode": state.data_mode,
        "sources": [
            {"name": "Weather (Open-Meteo, live, no key needed)",
             "status": w_status["status"], "last_updated": w_status["last_updated"]},
            {"name": "Risk history (SQLite, survives restarts)", "status": "CONNECTED", "last_updated": None},
            {"name": "Satellite (Sentinel-2 / Landsat / GEE)", "status": "NOT CONFIGURED", "last_updated": None},
            {"name": "IoT Sensors", "status": "NOT CONFIGURED", "last_updated": None},
            {"name": "Zone land-cover values (hand-set priors, UNVERIFIED)", "status": "ESTIMATED", "last_updated": None},
            {"name": "Synthetic Training Dataset", "status": "AVAILABLE", "last_updated": "generated locally"},
            {"name": "GenAI recommendations (Gemini / Claude)",
             "status": (f"CONFIGURED ({provider})" if provider else "NOT CONFIGURED (rule-based)"),
             "last_updated": None},
        ],
        "note": "See docs/DATA_SOURCES.md for how to connect each real source.",
    }


# ------------------------------------------------------ model performance -
@app.get("/api/model-performance")
def model_performance():
    if not state.metadata:
        raise HTTPException(503, "model metadata not available -- run ml/train.py")
    return {"data_mode": state.data_mode, **state.metadata, "residual_sample": state.residuals}


# ------------------------------------------------------------------ predict
class PredictInput(BaseModel):
    air_temp: float = Field(ge=-10, le=60)
    surface_temp: float = Field(ge=-10, le=85)
    humidity: float = Field(ge=0, le=100)
    wind_speed: float = Field(ge=0, le=60)
    ndvi: float = Field(ge=0, le=1)
    built_up_density: float = Field(ge=0, le=1)
    road_density: float = Field(ge=0, le=1)
    water_proximity: float = Field(ge=0, le=1)


def _category(risk):
    if risk >= 86:
        return "Extreme"
    if risk >= 71:
        return "Very High"
    if risk >= 51:
        return "High"
    if risk >= 26:
        return "Moderate"
    return "Low"


@app.post("/api/predict")
def predict(payload: PredictInput, x_api_key: str = Header(default=None)):
    required = os.environ.get("HEATSHIELD_API_KEY")
    if required and not (x_api_key and secrets.compare_digest(x_api_key, required)):
        raise HTTPException(401, "missing or invalid X-API-Key")
    row = {f: getattr(payload, f) for f in FEATURES}
    risk = state._predict_rows([row])[0]
    return {"data_mode": state.data_mode, "risk_score": round(risk, 1), "category": _category(risk)}


# ----------------------------------------------------------- recommendation
_rec_cache = {}
_rec_lock = threading.Lock()


@app.get("/api/recommendations/{zone_id}")
def recommendations(zone_id: str):
    """Cached per zone for HEATSHIELD_REC_TTL seconds (default 600) so that
    page refreshes / many clients can never multiply paid Claude API calls."""
    _require_zone(zone_id)
    ttl = float(os.environ.get("HEATSHIELD_REC_TTL", 600))
    now = time.time()
    with _rec_lock:
        hit = _rec_cache.get(zone_id)
        if hit and now - hit[0] < ttl:
            return {"data_mode": state.data_mode, **hit[1], "cached": True}
    zone = ZONE_BY_ID[zone_id]
    feats = state.zone_snapshot(zone_id)
    rec = get_recommendation(zone["name"], feats,
                             feature_importance=state.feature_importance_pct(),
                             drivers=state.explain_zone(zone_id)["drivers"])
    with _rec_lock:
        _rec_cache[zone_id] = (now, rec)
    return {"data_mode": state.data_mode, **rec, "cached": False}


# --------------------------------------------------------------- websocket
MAX_WS = int(os.environ.get("HEATSHIELD_MAX_WS", 50))
MAX_WS_PER_IP = int(os.environ.get("HEATSHIELD_MAX_WS_PER_IP", 5))
_ws_count = 0
_ws_by_ip = defaultdict(int)


def _origin_ok(websocket: WebSocket) -> bool:
    """Browsers always send Origin on WebSocket. Block other websites from
    opening our live feed (cross-site WebSocket hijacking)."""
    origin = websocket.headers.get("origin")
    if not origin:
        return True                                  # non-browser client (curl, tests)
    host = websocket.headers.get("host", "")
    return origin in ALLOWED_ORIGINS or origin.split("://", 1)[-1] == host


@app.websocket("/ws/live")
async def ws_live(websocket: WebSocket):
    global _ws_count
    ip = websocket.client.host if websocket.client else "unknown"
    if not _origin_ok(websocket):
        await websocket.close(code=1008)          # policy violation
        return
    if _ws_count >= MAX_WS or _ws_by_ip[ip] >= MAX_WS_PER_IP:
        await websocket.close(code=1013)          # try again later
        return
    await websocket.accept()
    _ws_count += 1
    _ws_by_ip[ip] += 1
    try:
        while True:
            # to_thread: the snapshot may do a (cached, 4 s timeout) network
            # call for weather; never block the event loop with it.
            snapshot = await asyncio.to_thread(state.get_snapshot)
            zones_out = [_zone_public(zid, f) for zid, f in snapshot.items()]
            avg_risk = round(sum(z["risk_score"] for z in zones_out) / len(zones_out), 1)
            spots, citywide_event = detect_hotspots({zid: f["risk_score"] for zid, f in snapshot.items()})
            for h in spots:
                h["zone_name"] = ZONE_BY_ID[h["zone_id"]]["name"]
            await websocket.send_json({
                "type": "live_update",
                "data_mode": state.data_mode,
                "model_algorithm": state.algorithm,
                "timestamp": time.time(),
                "avg_heat_risk": avg_risk,
                "critical_hotspots": len(spots),
                "citywide_heatwave_detected": citywide_event,
                "zones": zones_out,
                "hotspots": spots[:5],
            })
            await asyncio.sleep(3)
    except (WebSocketDisconnect, RuntimeError):
        pass
    except ModelNotAvailable as exc:
        await websocket.close(code=1011, reason=str(exc)[:100])
    finally:
        _ws_count -= 1
        _ws_by_ip[ip] -= 1
        if _ws_by_ip[ip] <= 0:
            _ws_by_ip.pop(ip, None)


# Serve the dashboard from the same origin (no CORS / hard-coded URL needed).
# Mounted LAST so it never shadows /api/* or /ws/*.
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=os.environ.get("HEATSHIELD_HOST", "127.0.0.1"), port=8000, reload=False)
