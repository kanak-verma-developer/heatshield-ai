# Architecture

```
 Open-Meteo (real weather, optional)  ──►  weather.py  (cached, thread-safe, 4 s timeout)
                                                │ unreachable → DEMO simulation (flagged)
                                                ▼
 data/zones.py (hand-set zone priors)  ──►  backend/services/state.py
                                                │  one shared snapshot (≤ 1 recompute / 2 s)
                                                │  history: 1 point / 60 s  ──►  SQLite (db.py)
                                                ├──► backend/models/heat_risk_model.joblib  (trained model)
                                                ├──► ml/hotspot_detection.py  (z-score OR absolute ≥ 71)
                                                └──► ml/forecasting.py        (offline fallback only)
                                                ▼
 backend/main.py (FastAPI)
      ├── REST  /api/*   (rate-limited, validated, CORS allow-list)
      ├── WebSocket /ws/live  (push every 3 s, capped)
      └── static dashboard at /   (frontend/index.html)
```

## Key design rules
- **Reads have no side effects.** REST calls and WebSocket clients all read the
  same cached snapshot; only the snapshot logic writes history, at a fixed interval.
- **No fabricated numbers.** No random noise; if the model can't be loaded the
  API answers 503; the dashboard never invents data when the backend is down
  (it shows a banner and reconnects automatically).
- **Honest labelling.** `data_mode` on every response; zone land-cover values are
  documented as unverified priors; the Model Performance page shows the
  synthetic noise ceiling next to R².
- **Real-time means server-computed.** The WebSocket loop runs the actual model
  and detector on the shared snapshot; the browser only renders what it receives.
  (Between weather updates the numbers legitimately change little — in DEMO
  mode the simulated clock runs `HEATSHIELD_SIM_SPEEDUP`× faster so the demo evolves.)

## Production-scale extensions (not built)
- **PostGIS** for real zone polygons and spatial queries.
- **Redis** for shared caching / rate limiting / WebSocket fan-out across instances.
- **APScheduler / Celery** for scheduled satellite ingestion.
- **Auth** for municipal users and an action-tracking workflow.
