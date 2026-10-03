# API Reference

Base URL: `http://localhost:8000` — the dashboard is served at `/`.
Interactive docs (FastAPI): `http://localhost:8000/docs`

Every JSON response includes `"data_mode"`: `"LIVE"` (real Open-Meteo weather
is currently reachable) or `"DEMO"` (simulated weather). In both modes the
zone land-cover values are hand-set priors.

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Uptime, model loaded?, algorithm, model error/warning, data mode |
| GET | `/api/status` | Per-component truth: `level` OK / DEMO / ESTIMATE / WARN / ERROR / MISSING / INFO + message, and an `overall` level |
| GET | `/api/current` | City snapshot: avg temp/risk, hotspot count, `citywide_heatwave_detected`, all zones |
| GET | `/api/zones` | All zones with current readings |
| GET | `/api/zones/{zone_id}` | One zone + `risk_explanation` + `drivers` (risk points vs an average zone) + global `feature_importance` |
| GET | `/api/heatmap` | Lightweight lat/lon/risk points |
| GET | `/api/hotspots` | Zones that are a z-score outlier (≥1.5σ) **or** have risk ≥ 71 |
| GET | `/api/forecast?zone_id=&hours=` | `hours` 1–48 (else 422). Model run on Open-Meteo's hourly forecast; trend fallback when offline (`method` says which) |
| GET | `/api/history?zone_id=` | Time series (`timestamps`, `risk_history`), one point per `HEATSHIELD_HISTORY_INTERVAL` s. Without `zone_id`: all zones + `city_average` |
| GET | `/api/data-sources` | Status of each data source |
| GET | `/api/model-performance` | Model metadata: MAE/RMSE/R², `synthetic_noise_ceiling_r2`, importance, residual sample |
| POST | `/api/predict` | Run the model on a custom feature vector (range-validated; optional `X-API-Key`) |
| GET | `/api/recommendations/{zone_id}` | `source` is `RULE_BASED`, `GEMINI_AI` or `CLAUDE_AI`; cached per zone (`"cached"` flag) |
| WS | `/ws/live` | Pushes a full city snapshot every 3 s (max `HEATSHIELD_MAX_WS` clients) |

## Status codes
`404` unknown zone · `422` invalid parameter/body · `401` bad/missing API key
(only if `HEATSHIELD_API_KEY` is set) · `429` rate limit (`HEATSHIELD_RATE_LIMIT_PER_MIN`,
per IP, `/api/*` only) · `503` model not available (never a made-up number).

## Example: `POST /api/predict`
Valid ranges: `air_temp` −10…60, `surface_temp` −10…85, `humidity` 0…100,
`wind_speed` 0…60, `ndvi`, `built_up_density`, `road_density`, `water_proximity` 0…1.
```json
{ "air_temp": 38, "surface_temp": 52, "humidity": 25, "wind_speed": 1.2,
  "ndvi": 0.08, "built_up_density": 0.88, "road_density": 0.75, "water_proximity": 0.1 }
```
→ `{"data_mode": "DEMO", "risk_score": 68.2, "category": "High"}`

## Example: `/zones/{id}` explanation fields
```json
{
  "risk_explanation": "Budh Bazaar scores 51/100, 12 points above the city average. According to the model, built-up density (0.88 vs city mean 0.672) adds about 7.2 points and ...",
  "drivers": [ { "feature": "built_up_density", "label": "built-up density",
                 "zone_value": 0.88, "city_mean": 0.672, "risk_points_vs_city_avg": 7.2 } ],
  "method": "counterfactual re-prediction vs city-average zone priors"
}
```

## Example: `/ws/live` message
```json
{
  "type": "live_update", "data_mode": "DEMO", "model_algorithm": "Ridge",
  "timestamp": 1790966576.1, "avg_heat_risk": 35.7, "critical_hotspots": 1,
  "citywide_heatwave_detected": false,
  "zones": [ { "zone_id": "civil_lines", "zone_name": "Civil Lines", "risk_score": 43.2, "...": "..." } ],
  "hotspots": [ { "zone_id": "moradabad_central", "zone_name": "Moradabad Central",
                  "anomaly_score": 1.57, "severity": "MODERATE", "trigger": "relative_outlier" } ]
}
```
