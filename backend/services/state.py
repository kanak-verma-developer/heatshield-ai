"""
Central runtime state for HeatShield AI backend.

Design notes
------------
* ONE shared city snapshot. `get_snapshot()` recomputes at most every
  SNAPSHOT_MAX_AGE seconds no matter how many REST calls / WebSocket
  clients ask for it. Reading data never has side effects on history.
* History is recorded by the snapshot logic at most once per
  HISTORY_INTERVAL seconds (default 60) for the whole city, so
  /api/history is a real, evenly spaced time series. Nothing is fabricated:
  on a brand-new install the history simply starts empty.
* No random noise. Live mode = real Open-Meteo weather + fixed zone priors.
  DEMO mode (weather unreachable) = deterministic physics-motivated
  simulation whose clock runs SIM_SPEEDUP x faster than real time so the
  demo visibly evolves. DEMO is always flagged via `data_mode`.
* Zone attributes (built-up density, NDVI, road density, water proximity)
  are hand-set PRIORS (see data/zones.py), not measurements.
* If the model file is missing/unloadable, prediction raises
  ModelNotAvailable -- the API returns 503 instead of inventing a number.
"""
import json
import math
import os
import sys
import threading
import time
from datetime import datetime

import joblib
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from data.zones import ZONES, ZONE_BY_ID
from ml.forecasting import forecast_zone
from backend.services.weather import get_live_weather, get_weather_forecast
from backend.services import db as history_db

BASE = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE, "..", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "heat_risk_model.joblib")
META_PATH = os.path.join(MODEL_DIR, "model_metadata.json")
RESIDUALS_PATH = os.path.join(MODEL_DIR, "residuals_sample.json")

FEATURES = ["air_temp", "surface_temp", "humidity", "wind_speed",
            "ndvi", "built_up_density", "road_density", "water_proximity"]

FEATURE_LABELS = {
    "built_up_density": "built-up density",
    "ndvi": "vegetation cover (NDVI)",
    "road_density": "road/paved-surface density",
    "water_proximity": "proximity to water",
}

SNAPSHOT_MAX_AGE = float(os.environ.get("HEATSHIELD_SNAPSHOT_MAX_AGE", 2.0))
HISTORY_INTERVAL = float(os.environ.get("HEATSHIELD_HISTORY_INTERVAL", 60))
HISTORY_LEN = 288          # points kept per zone in memory (~4.8 h at 60 s)
SIM_SPEEDUP = float(os.environ.get("HEATSHIELD_SIM_SPEEDUP", 60))  # DEMO mode only


class ModelNotAvailable(RuntimeError):
    pass


class HeatShieldState:
    def __init__(self):
        self._lock = threading.RLock()
        self.model = None
        self.model_error = None
        self.model_warning = None
        self.metadata = {}
        self.residuals = []
        self._load_model()

        self.live_weather = None            # last successful real reading, or None
        self._snapshot = None
        self._snapshot_ts = 0.0
        self._snapshot_weather = None
        self._last_history_ts = 0.0
        self.last_forecast_method = None     # "live" | "trend_fallback" | None (never requested)
        self.history = {z["id"]: [] for z in ZONES}   # zone_id -> [(ts, score)]

        history_db.init_db()
        history_db.prune_old()
        for z in ZONES:
            self.history[z["id"]] = history_db.load_recent(z["id"], limit=HISTORY_LEN)
        # If history was restored, don't immediately write a duplicate point.
        restored = [h[-1][0] for h in self.history.values() if h]
        if restored:
            self._last_history_ts = max(restored)

    # ------------------------------------------------------------ model ---
    def _load_model(self):
        try:
            if os.path.exists(META_PATH):
                with open(META_PATH) as f:
                    self.metadata = json.load(f)
            if os.path.exists(RESIDUALS_PATH):
                with open(RESIDUALS_PATH) as f:
                    self.residuals = json.load(f)
            if not os.path.exists(MODEL_PATH):
                self.model_error = "model file missing -- run `python ml/train.py`"
                return
            import sklearn
            trained_with = self.metadata.get("sklearn_version")
            if trained_with and trained_with != sklearn.__version__:
                self.model_warning = (
                    f"model trained with scikit-learn {trained_with} but running "
                    f"{sklearn.__version__}; re-run `python ml/train.py` if predictions look wrong"
                )
                print(f"[state] WARNING: {self.model_warning}")
            self.model = joblib.load(MODEL_PATH)
        except Exception as exc:  # noqa: BLE001
            self.model = None
            self.model_error = f"could not load model ({exc}); re-run `python ml/train.py`"
            print(f"[state] ERROR: {self.model_error}")

    def model_ready(self):
        return self.model is not None

    def _predict_rows(self, rows):
        if self.model is None:
            raise ModelNotAvailable(self.model_error or "model not loaded")
        df = pd.DataFrame([[r[f] for f in FEATURES] for r in rows], columns=FEATURES)
        return [max(0.0, min(100.0, float(p))) for p in self.model.predict(df)]

    @property
    def algorithm(self):
        return self.metadata.get("algorithm", "unknown")

    # --------------------------------------------------------- weather ----
    def _current_weather(self, now):
        """City-wide weather: real Open-Meteo reading, or the DEMO simulation."""
        live = get_live_weather()
        self.live_weather = live
        if live is not None:
            return {"air_temp": live["air_temp"], "humidity": live["humidity"],
                    "wind_speed": live["wind_speed"]}
        # DEMO: deterministic simulation, clock accelerated by SIM_SPEEDUP.
        sim_t = now * SIM_SPEEDUP
        hour = (sim_t / 3600.0) % 24
        doy = datetime.fromtimestamp(now).timetuple().tm_yday
        seasonal = 32 + 8 * math.sin(2 * math.pi * doy / 365.0 - 1.4)   # same curve as training
        diurnal = 6 * math.sin((hour - 6) / 24 * 2 * math.pi)
        return {
            "air_temp": seasonal + diurnal,
            "humidity": 55 - 10 * math.sin((hour - 6) / 24 * 2 * math.pi),
            "wind_speed": 2.4 + 0.8 * math.sin(sim_t / 3600.0 * 0.7),
        }

    @property
    def data_mode(self):
        """LIVE when real weather is currently reachable, DEMO otherwise."""
        return "LIVE" if self.live_weather is not None else "DEMO"

    # -------------------------------------------------------- features ----
    @staticmethod
    def _zone_weather(zone, w):
        """City weather -> zone weather using a small, physically motivated
        urban-heat-island prior (an assumption, not per-zone sensor data)."""
        b, wp = zone["built_up_density"], zone["water_proximity"]
        return {
            "air_temp": w["air_temp"] + 1.8 * (b - 0.5) - 1.0 * wp,
            "humidity": max(10, min(95, w["humidity"] - 10 * (b - 0.5) + 8 * wp)),
            "wind_speed": max(0.2, w["wind_speed"] * (1.0 - 0.15 * b)),
        }

    @classmethod
    def _features_for(cls, zone, w):
        zw = cls._zone_weather(zone, w)
        b, ndvi = zone["built_up_density"], max(0.02, zone["ndvi_base"])
        rd, wp = zone["road_density"], zone["water_proximity"]
        surface_temp = (zw["air_temp"] + 9.0 * b - 7.0 * ndvi + 3.0 * rd
                        - 2.5 * wp - 0.6 * zw["wind_speed"])
        return {
            "air_temp": round(zw["air_temp"], 2),
            "surface_temp": round(surface_temp, 2),
            "humidity": round(zw["humidity"], 1),
            "wind_speed": round(zw["wind_speed"], 2),
            "ndvi": round(ndvi, 3),
            "built_up_density": round(b, 3),
            "road_density": round(rd, 3),
            "water_proximity": round(wp, 3),
        }

    # -------------------------------------------------------- snapshot ----
    def get_snapshot(self, max_age=None):
        """{zone_id: features+risk_score}, shared by every caller."""
        max_age = SNAPSHOT_MAX_AGE if max_age is None else max_age
        with self._lock:
            now = time.time()
            if self._snapshot is not None and (now - self._snapshot_ts) < max_age:
                return self._snapshot
            weather = self._current_weather(now)
            feats = {z["id"]: self._features_for(z, weather) for z in ZONES}
            risks = self._predict_rows([feats[z["id"]] for z in ZONES])
            snap = {}
            for z, risk in zip(ZONES, risks):
                snap[z["id"]] = {**feats[z["id"]], "risk_score": round(risk, 2)}
            self._snapshot, self._snapshot_ts, self._snapshot_weather = snap, now, weather
            if now - self._last_history_ts >= HISTORY_INTERVAL:
                self._record_history(snap, now)
            return snap

    tick = get_snapshot   # backwards-compatible alias

    def zone_snapshot(self, zone_id):
        return self.get_snapshot()[zone_id]

    def _record_history(self, snap, now):
        scores = {zid: f["risk_score"] for zid, f in snap.items()}
        for zid, score in scores.items():
            h = self.history[zid]
            h.append((now, score))
            if len(h) > HISTORY_LEN:
                h.pop(0)
        self._last_history_ts = now
        history_db.save_readings(now, scores)

    def zone_history(self, zone_id):
        with self._lock:
            return list(self.history[zone_id])

    def city_average_history(self):
        """[(ts, avg_risk)] over timestamps at which every zone has a reading."""
        with self._lock:
            by_ts = {}
            for h in self.history.values():
                for ts, score in h:
                    by_ts.setdefault(ts, []).append(score)
            n = len(ZONES)
            return [(ts, round(sum(v) / len(v), 2)) for ts, v in sorted(by_ts.items()) if len(v) == n]

    # ----------------------------------------------------- explanation ----
    def feature_importance_pct(self):
        fi = self.metadata.get("feature_importance", {})
        total = sum(fi.values()) or 1
        return {k: round(v / total * 100, 1) for k, v in fi.items()}

    def explain_zone(self, zone_id):
        """Zone-specific, MODEL-DRIVEN explanation (counterfactual).

        For each zone attribute (built-up density, NDVI, road density,
        water proximity) the model is re-run with that attribute replaced by
        the city-wide mean of the zone priors (surface temperature and the
        urban-heat-island adjustments are recomputed consistently). The
        change in predicted risk is that attribute's contribution relative to
        an 'average Moradabad zone' -- in risk points, not a global
        importance percentage."""
        zone = ZONE_BY_ID[zone_id]
        self.get_snapshot()
        weather = self._snapshot_weather
        actual = self._predict_rows([self._features_for(zone, weather)])[0]
        keys = {"built_up_density": "built_up_density", "ndvi": "ndvi_base",
                "road_density": "road_density", "water_proximity": "water_proximity"}
        means = {k: sum(z[v] for z in ZONES) / len(ZONES) for k, v in keys.items()}
        counterfactuals = []
        for k, zkey in keys.items():
            alt = dict(zone)
            alt[zkey] = means[k]
            counterfactuals.append(self._features_for(alt, weather))
        alts = self._predict_rows(counterfactuals)
        drivers = []
        for (k, zkey), alt_risk in zip(keys.items(), alts):
            drivers.append({
                "feature": k,
                "label": FEATURE_LABELS[k],
                "zone_value": round(zone[zkey], 3),
                "city_mean": round(means[k], 3),
                "risk_points_vs_city_avg": round(actual - alt_risk, 1),
            })
        drivers.sort(key=lambda d: -abs(d["risk_points_vs_city_avg"]))
        city_avg = sum(self.get_snapshot()[z["id"]]["risk_score"] for z in ZONES) / len(ZONES)
        text = self._explanation_text(zone["name"], actual, city_avg, drivers)
        return {"risk_explanation": text, "drivers": drivers,
                "method": "counterfactual re-prediction vs city-average zone priors"}

    @staticmethod
    def _explanation_text(name, risk, city_avg, drivers):
        diff = risk - city_avg
        head = (f"{name} scores {risk:.0f}/100, "
                + ("close to" if abs(diff) < 1 else f"{abs(diff):.0f} points {'above' if diff > 0 else 'below'}")
                + " the city average.")
        top = [d for d in drivers if abs(d["risk_points_vs_city_avg"]) >= 0.5][:2]
        if not top:
            return head + " None of its land-cover priors differs much from the city average."
        parts = []
        for d in top:
            pts = d["risk_points_vs_city_avg"]
            parts.append(f"{d['label']} ({d['zone_value']} vs city mean {d['city_mean']}) "
                         f"{'adds' if pts > 0 else 'removes'} about {abs(pts):.1f} points")
        return head + " According to the model, " + " and ".join(parts) + "."

    # -------------------------------------------------------- forecast ----
    def forecast_zone_ml(self, zone_id, hours_ahead=6):
        """Run the trained model on Open-Meteo's real hourly forecast; fall
        back to trend extrapolation of recent history if unreachable."""
        zone = ZONE_BY_ID.get(zone_id)
        wf = get_weather_forecast(hours_ahead) if zone else None
        if zone is not None and wf is not None and self.model is not None:
            rows = [self._features_for(zone, row) for row in wf]
            risks = self._predict_rows(rows)
            base_rmse = self.metadata.get("metrics", {}).get("rmse", 3.5)
            out = []
            for row, risk in zip(wf, risks):
                # Interval widens with horizon, anchored to the model's test RMSE.
                # NOTE: that RMSE is measured on synthetic data, so this is an
                # illustrative band, not a calibrated prediction interval.
                u = base_rmse * (1 + 0.15 * row["hour_offset"])
                out.append({
                    "hour": row["hour_offset"],
                    "predicted_risk": round(risk, 1),
                    "lower": round(max(0, risk - u), 1),
                    "upper": round(min(100, risk + u), 1),
                    "source": "ml_model+live_forecast",
                })
            self.last_forecast_method = "live"
            return out, "live"
        self.get_snapshot()   # make sure at least one reading exists
        recent = [s for _, s in self.zone_history(zone_id)][-12:]
        self.last_forecast_method = "trend_fallback"
        return forecast_zone(recent, hours_ahead=hours_ahead), "trend_fallback"


state = HeatShieldState()
