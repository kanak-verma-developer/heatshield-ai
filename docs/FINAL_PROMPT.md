# HeatShield AI — Final Master Spec
**AI/ML-based urban heat intelligence, prediction & mitigation platform for Moradabad**

Single reference for design, features, technology and accuracy — matching
what is implemented in this repository (see `CHANGELOG.md` for history).

---

## 1. Design
Dark "climate command center" dashboard (`frontend/index.html`, served by the backend at `/`):
- **Sidebar:** Overview, Forecast, Model Performance, Data Sources + live data-status box.
- **Header:** connection pulse (green = backend connected, orange = demo data, red = offline),
  last-updated time, current temperature, city heat-risk ring.
- **KPI row:** temperature, average risk, hotspot count, max surface temp, average NDVI, model name (read from the backend).
- **Center:** Leaflet/OpenStreetMap map (grid-map fallback if the CDN is blocked) with 11 zone markers
  coloured by risk; zone panel with risk donut, metrics, a model-driven explanation and per-zone drivers.
- **Bottom row:** server-side city-average trend, hotspot list, recommendations.
- When the backend is down: red banner + automatic reconnect; no numbers are fabricated in the browser.

## 2. Features
- ✅ Live dashboard over a real WebSocket (`/ws/live`, 3 s)
- ✅ Trained ML model (best of RandomForest / GradientBoosting / Ridge / ElasticNet; currently **Ridge**)
- ✅ Hotspot detection: z-score outlier OR absolute risk ≥ 71 (+ city-wide heatwave flag)
- ✅ Forecast: model run on Open-Meteo's real hourly forecast (1–48 h), trend fallback offline
- ✅ Model-driven per-zone explanation (counterfactual vs average zone, in risk points)
- ✅ Rule-based recommendations; Gemini- or Claude-generated when a key is set (validated, cached per zone)
- ✅ Honest status labels: `/api/status` + badges on every card (REAL / DEMO / ESTIMATE / CHECK / ERROR / NOT CONNECTED), stale-data watchdog, visible load errors
- ✅ Persistent history (SQLite, 1 point/min, 7-day retention)
- ✅ Model-performance page incl. synthetic noise ceiling; data-sources page
- ✅ Rate limiting, CORS allow-list, optional API key, input validation, Docker + healthcheck, 68 tests
- 🔲 Real satellite / IMD / IoT data (see `DATA_SOURCES.md`)
- 🔲 Verified zone land-cover values and real ward polygons
- 🔲 SHAP, PostGIS, auth, mitigation-action tracking

## 3. Technology
| Layer | Technology |
|---|---|
| Frontend | HTML/CSS/vanilla JS, Chart.js + Leaflet (bundled locally), OpenStreetMap tiles |
| Backend | Python, FastAPI, Uvicorn, Pydantic, WebSockets |
| ML | scikit-learn (RandomizedSearchCV), pandas, numpy, scipy, joblib |
| Weather | Open-Meteo (free, no key) |
| GenAI | Google Gemini API or Anthropic Claude API (optional) |
| Persistence | SQLite |
| Not built | PostGIS, Redis, Earth Engine / Sentinel-2 ingestion |

## 4. Accuracy — what the numbers do and do not mean
From the committed run (`backend/models/model_metadata.json`; time-aware 80/20 split on **synthetic** data):

| Model | Test MAE | Test RMSE | Test R² |
|---|---|---|---|
| RandomForest | 2.896 | 3.613 | 0.8755 |
| GradientBoosting | 2.876 | 3.593 | 0.8769 |
| **Ridge (selected)** | **2.842** | **3.545** | **0.8801** |
| ElasticNet | 2.842 | 3.546 | 0.8801 |

**Synthetic noise ceiling: R² = 0.8805.** The target is a known formula plus
noise, so the best any model can do is ≈ 0.88; Ridge reaches it, which shows the
pipeline can recover a known relationship. It is **not** real-world accuracy and
must not be presented as "88% accuracy". Real accuracy requires real
Moradabad data (see `DATA_SOURCES.md`) — the ML/API code does not need to change.

Zone differences come from hand-set, unverified land-cover priors, so the zone
ranking and hotspot list reflect those assumptions, not measurements.
