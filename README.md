# HeatShield AI
**AI-powered urban heat intelligence & mitigation dashboard — Moradabad, Uttar Pradesh, India**

A working FastAPI + WebSocket backend, a trained scikit-learn model, hotspot
detection, a model-based forecast and a live dashboard. Current weather is real
(Open-Meteo); **zone land-cover values are hand-set priors and the model is trained
on synthetic data** — see §1 and `docs/MODEL_CARD.md` before quoting any number.

Docs: `docs/NEXT_STEPS.md` (checklist) · `docs/MODEL_CARD.md` · `docs/API.md` · `docs/ARCHITECTURE.md` ·
`docs/DATA_SOURCES.md` · `docs/FINAL_PROMPT.md` · `docs/CHANGELOG.md`

---

## 1. What is real vs demo

| Component | Status |
|---|---|
| ML model (scikit-learn, tuned with RandomizedSearchCV) | ✅ Real training code — on **synthetic** data |
| Reported R² ≈ 0.88 | ⚠️ Equals the data's own noise ceiling (0.8805): the model recovered the formula that made the data. **Not real-world accuracy.** |
| FastAPI backend, REST, WebSocket `/ws/live` | ✅ Real; server-computed every 3 s |
| Hotspot detection (z-score OR risk ≥ 71) | ✅ Real method; zone ranking is driven by fixed priors, so the same dense zones usually top the list |
| Forecast (1–48 h) | ✅ Model run on Open-Meteo's real hourly forecast; trend fallback offline |
| Per-zone explanation | ✅ Model-driven (counterfactual vs average zone, in risk points) |
| Current air temp / humidity / wind | ✅ **Real** (Open-Meteo, cached 10 min) — `LIVE` mode |
| Weather when Open-Meteo is unreachable | 🟠 Deterministic simulation — `DEMO` mode (always flagged) |
| Zone NDVI / built-up / road density / water proximity | 🟠 **Hand-set, unverified priors** (`data/zones.py`) |
| Surface temperature | 🟠 Computed from air temp + priors (not a satellite LST) |
| Zone map shapes | 🟠 Point markers at approximate coordinates, not ward polygons |
| AI recommendations | 🟠 Rule-based unless `GEMINI_API_KEY` (or `ANTHROPIC_API_KEY`) is set; cached per zone |
| Satellite / IoT data | 🔲 Not connected |

`data_mode` is computed on every request (`LIVE` only while real weather is
being received) and shown in the dashboard.

---

### Status labels on the dashboard (nothing demo is hidden)
The **Data Quality & System Status** panel (Overview) and small badges on each card
come from `GET /api/status`:

| Badge | Meaning | Examples |
|---|---|---|
| 🟢 **OK** | real and working | live Open-Meteo weather; forecast built from the real hourly forecast; reply written by Gemini |
| 🟠 **DEMO** | simulated / synthetic | simulated weather (Open-Meteo unreachable); model trained on synthetic data |
| 🟡 **ESTIMATE** | assumption, not measured | zone land-cover values; computed surface temperature; trend-extrapolated forecast; rule-based recommendations |
| 🔴 **CHECK** | degraded — look into it | weather data >20 min old; Gemini call failed (rule-based fallback shown); scikit-learn version mismatch; `STALE` (no update for >10 s) |
| ⛔ **ERROR** | broken | model not loaded (API answers 503) ; backend offline |
| ⚪ **NOT CONNECTED** | not available yet | satellite / IoT sensors |

Failures are shown, never swallowed: if zone details, recommendations, forecast, data
sources or model metrics cannot be loaded, the card says so (and whether the backend is
unreachable or returned an error).

## 2. Folder structure
```
heatshield-ai/
├── backend/
│   ├── main.py                    # FastAPI: REST + WebSocket + serves the dashboard
│   ├── requirements.txt / requirements-dev.txt
│   ├── services/  state.py  weather.py  recommendations.py  db.py
│   └── models/                    # heat_risk_model.joblib + model_metadata.json (committed)
├── ml/                            # generate_dataset.py  train.py  hotspot_detection.py  forecasting.py
├── data/                          # zones.py (priors)  training_data.csv  heatshield_history.db (created at runtime)
├── frontend/index.html            # the dashboard
│   └── vendor/                    # Chart.js + Leaflet, bundled locally (no CDN needed)
├── tests/                         # 68 tests
├── docs/                          # model card, API, architecture, data sources, changelog
├── Dockerfile  .dockerignore  .env.example  .gitignore
```

## 3. Run it (Python 3.10+)

```bash
# 1. install (from the project root)
pip install -r backend/requirements.txt

# 2. (optional) retrain — a trained model is already included
python ml/generate_dataset.py
python ml/train.py            # prints MAE/RMSE/R² AND the synthetic noise ceiling

# 3. start backend + dashboard
uvicorn backend.main:app --port 8000
```
Open **http://localhost:8000/** (API docs at `/docs`, health at `/api/health`).

- You can also open `frontend/index.html` directly (it talks to `http://localhost:8000`),
  or point it elsewhere with `index.html?api=https://your-host`.
- If the backend is stopped, the dashboard shows a red banner and reconnects by itself.
- The scikit-learn version should match the one in `model_metadata.json`; the backend
  prints a warning otherwise — just re-run `python ml/train.py`.
- In LIVE mode values change only when the weather changes (every ~10–15 min).
  In DEMO mode the simulated day runs 60× faster so the demo visibly moves
  (`HEATSHIELD_SIM_SPEEDUP`).

### Optional: AI recommendations (Gemini or Claude)
No key is needed to run the project. To get LLM-written recommendations:

1. Copy `.env.example` to `.env` (in the project root) and fill in **one** key:
   ```
   GEMINI_API_KEY=your-key-from-aistudio.google.com/apikey
   ```
   (or `ANTHROPIC_API_KEY=...` for Claude). `.env` is git-ignored and is loaded
   automatically at start-up; real environment variables take priority.
2. Start the backend. The dashboard's recommendation card then says `(Gemini AI)`;
   `/api/data-sources` shows `CONFIGURED (gemini)`.
3. If Google renames/retires the default model (`gemini-2.5-flash`), set
   `GEMINI_MODEL=<current model name>` in `.env`.
4. If both keys are set, Gemini is used unless `HEATSHIELD_LLM_PROVIDER=claude`.

At most one LLM call per zone per `HEATSHIELD_REC_TTL` seconds (default 600). If a
call fails (quota, network, bad reply) the rule-based answer is shown and flagged.
The model only receives numbers the system already computed (zone name + features).
Never commit your `.env` or paste keys into the code.

### Configuration
See `.env.example` (CORS origins, rate limit, WebSocket cap, `/api/predict` API key,
history interval, …). Defaults are safe for local use.

### Docker
```bash
docker build -t heatshield-ai .
docker run -p 8000:8000 heatshield-ai      # dashboard + API at http://localhost:8000/
```

### Tests
```bash
pip install -r backend/requirements-dev.txt
pytest tests/ -v          # from the project root; no network or API key needed
# (run `python ml/train.py` once first so the saved model matches your scikit-learn version)
```

---

## 4. Known limitations (please read before presenting)
1. **Model quality is unverified on real data.** Synthetic target + same inputs ⇒ the
   reported R² only shows the pipeline works.
2. **Zone differences = my priors.** `data/zones.py` values are unverified; rankings and
   "hotspots" mostly reflect them. Review them with local knowledge or replace them with
   Sentinel-2/Landsat-derived values (see `docs/DATA_SOURCES.md`).
3. Forecast uncertainty bands are illustrative (based on synthetic-data RMSE).
4. Rate limiting is per process and per IP (behind a proxy, use the proxy's limiter).
5. Chart.js and Leaflet are bundled in `frontend/vendor/`; only the OpenStreetMap map tiles need internet (offline: markers on a blank map or the built-in grid map).
6. No authentication on read endpoints; this is a demo-grade deployment.

## 5. What changed in the latest round
See `docs/CHANGELOG.md` (Round 6): single shared snapshot + throttled history,
forecast-cache fix, no per-tick refetch of paid recommendations, model-driven
explanations, honest model docs (Ridge, noise ceiling), hardened API, Docker fixes,
68 tests.
