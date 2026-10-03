# Data Sources — current status & how to go live

## Current status (today)

| Source | Status | Notes |
|---|---|---|
| Weather (Open-Meteo, live) | **CONNECTED** — no key/signup needed | real current temperature, humidity, wind for Moradabad |
| Satellite (Sentinel-2 / Landsat / Google Earth Engine) | NOT CONFIGURED | needs GEE service account or Copernicus access |
| IoT sensors | NOT CONFIGURED | no hardware deployed |
| Zone land-cover values (built-up, NDVI, road density, water proximity) | **ESTIMATED — hand-set priors, UNVERIFIED** | `data/zones.py`; not measured, drive most of the zone ranking |
| Synthetic training dataset | AVAILABLE | `data/training_data.csv` (365 days x 6/day x 11 zones) |
| GenAI recommendations (Gemini or Claude) | CONFIGURED only if `GEMINI_API_KEY` or `ANTHROPIC_API_KEY` is set | falls back to rule-based otherwise |

`GET /api/data-sources` reports this same table live — it checks the actual
environment (e.g. whether the Anthropic key is present) rather than
hardcoding "Connected".

## How to connect each real source without redesigning the frontend

The frontend/API contract (`air_temp, surface_temp, humidity, wind_speed,
ndvi, built_up_density, road_density, water_proximity` → `risk_score`) stays
the same regardless of where the numbers come from. To go live:

### 1. Weather (air_temp, humidity, wind_speed) — ✅ DONE
- **Implemented**: `backend/services/weather.py` calls **Open-Meteo**
  (`api.open-meteo.com`) — completely free, no signup, no API key — for
  Moradabad's real current temperature, humidity and wind speed.
- Result is cached for 10 minutes (`CACHE_SECONDS`); a failed request is
  retried at most every 30s (`RETRY_SECONDS`). The 48-hour hourly forecast is
  fetched once per 30 min and sliced per request.
- `backend/services/state.py` uses this real reading as the city-wide
  baseline for every zone, then applies a small, physically-motivated
  per-zone urban-heat-island offset (denser/paved zones run a bit
  hotter, water-adjacent zones a bit cooler) — the offset is a documented
  *prior*, same as the zone table, never claimed as a per-zone sensor.
- If Open-Meteo is unreachable (no internet, API down), `get_live_weather()`
  returns `None` and `state.py` automatically falls back to the old
  physics-motivated simulation. `state.data_mode` reflects this honestly as
  `"LIVE"` or `"DEMO"` on every single API response and in the dashboard's
  header/status box — nothing is ever silently mislabeled.
- **IMD (India Meteorological Department)** station data remains a possible
  future upgrade for higher local accuracy, but requires a data-sharing
  request and isn't needed to have genuinely real weather today.

### 2. Satellite (surface_temp / LST, ndvi, built_up_density / NDBI, water_proximity / NDWI)
- **Google Earth Engine** (Sentinel-2, Landsat 8/9 thermal bands): compute
  NDVI = (NIR-Red)/(NIR+Red), NDBI = (SWIR-NIR)/(SWIR+NIR), LST from thermal
  bands, NDWI = (Green-NIR)/(Green+NIR), per zone polygon.
  Requires a GEE service account (`google-earth-engine` or `earthengine-api`
  Python package) and zone boundaries as real GeoJSON polygons (the dashboard
  currently shows each zone as a point marker at its `lat/lon`; add real
  ward/locality polygons, e.g. from the OpenStreetMap Overpass API or
  Bhuvan, and draw those instead).
- These derived indices become a scheduled batch job (e.g. daily/weekly,
  since satellite revisit time is not sub-hourly) writing into the same
  feature columns the model already expects.

### 3. IoT sensors (optional, future)
- If/when physical sensors are deployed, they'd POST readings to a new
  ingestion endpoint (e.g. `/api/ingest/sensor`) that writes into the same
  feature schema, then `state.py` reads the latest sensor row instead of
  simulating it for that zone.

### 4. `data_mode` is dynamic (no manual flipping needed)
`HeatShieldState.data_mode` (a `@property` in `backend/services/state.py`)
returns `"LIVE"` automatically whenever the Open-Meteo weather fetch is
currently succeeding, and `"DEMO"` the moment it isn't — every API response
and the dashboard's header/status box reflect this in real time. Adding a
new real source (satellite, IoT) should follow the same pattern: track
whether *that* source is currently reachable, and only ever report "LIVE"
for the parts of the pipeline that are genuinely backed by it.

### 5. Gemini / Claude for recommendations
Already wired — put one key in `.env` (see `.env.example`) or the environment:
```bash
GEMINI_API_KEY=...        # default model gemini-2.5-flash, override with GEMINI_MODEL
# or: ANTHROPIC_API_KEY=sk-ant-...
```
`backend/services/recommendations.py` sends structured (already-computed)
zone data to the LLM and asks it to prioritize/explain — it never lets the
model invent temperature or NDVI numbers itself. Responses are cached per
zone for `HEATSHIELD_REC_TTL` seconds (default 600), so the number of paid
calls is bounded (at most one per zone per cache window) regardless of traffic.


### 6. Replacing the zone priors (the single most valuable upgrade)
Today the *only* thing that differs between zones is the hand-set table in
`data/zones.py`. Replacing it with Sentinel-2/Landsat-derived values per
zone polygon (step 2) is what turns the zone ranking and hotspot list from
"a property of my assumptions" into an actual finding.
