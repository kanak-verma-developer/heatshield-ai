## 1.3.0: UI, security, awareness video
- Logo splash animation with real startup checks (server, secure headers, data); shown once per session, skippable.
- Security: strict CSP (no inline scripts, JS moved to `frontend/app.js`), anti-framing, no-sniff, referrer and permissions headers, HSTS on HTTPS, no-store on API.
- Live feed: cross-site origin check and per-visitor connection cap. `file://` ("null") origin no longer allowed by default.
- API docs hidden unless `HEATSHIELD_ENABLE_DOCS=1`; server binds to 127.0.0.1 by default (`HEATSHIELD_HOST`).
- XSS fixes: data-source and model fields are now escaped; no inline event handlers.
- New `GET /api/security` and a "Security audit" panel in the dashboard.
- Silent awareness video card with rotating tips and an animated fallback when no video file exists.

# Changelog

## Round 9 — fixes found by running it on a real machine
- Trend/donut charts were blank when the Chart.js CDN was unreachable: Chart.js and Leaflet are now bundled in
  `frontend/vendor/` (licences included) and a visible `CHART LIBRARY NOT LOADED` badge appears if they still fail.
- Card headers no longer collapse (title / subtitle / badge layout), map labels no longer overlap
  (score only when zoomed out, name + score from zoom 14), KPI "Critical Hotspots" -> "Hotspot Zones"
  (a MODERATE-severity zone is not "critical"), Data Sources status colours for `CONFIGURED`.
- Verified `python ml/train.py` + the whole test-suite under scikit-learn 1.5.1 (what the user had installed).
- Tests: 66 -> 68.

## Round 8 — honest status labels everywhere
- New `GET /api/status` (per-component level OK/DEMO/ESTIMATE/WARN/ERROR/MISSING/INFO + plain message).
- Dashboard: status panel, header "System" chip, badges on map / zone / trend / hotspots / recommendations /
  forecast / model pages, `STALE` watchdog, and visible error messages instead of silent `.catch(()=>{})`.
- `/api/forecast` returns `data_quality` (`LIVE_FORECAST` | `ESTIMATE`); recommendation fallbacks return a `note`.
- `docs/NEXT_STEPS.md` checklist. Tests: 56 -> 66.

## Round 7 — Gemini support
- `GEMINI_API_KEY` enables Gemini-written recommendations (REST, key sent in a
  header, 15 s timeout, `GEMINI_MODEL` override); Claude still works; provider
  choice via `HEATSHIELD_LLM_PROVIDER`.
- LLM replies are validated/normalised (priority whitelist, list/str coercion,
  length caps) and fall back to the rule-based answer on any error; keys are never
  logged or returned.
- `.env` is now auto-loaded (real environment variables win). Tests: 44 -> 56.

## Round 6 — correctness, honesty and hardening

**Fixed (bugs)**
- Every REST call and every WebSocket client used to advance the model and write
  to the history DB (`state.tick()` per request). Now one shared snapshot
  (`get_snapshot`, max age 2 s) and history is recorded once per
  `HEATSHIELD_HISTORY_INTERVAL` (60 s) for the whole city. History is a real,
  time-stamped series; nothing is fabricated on first start.
- The dashboard re-fetched zone details **and recommendations every 3 s**
  (a paid Claude call per tick when a key was set). Details now load on
  selection and at most every 30 s; the API also caches recommendations per zone.
- Forecast cache ignored the requested horizon (a 6 h request first truncated
  later 24 h requests). The cache now holds the full 48 h window; `hours` is
  validated (1-48); `hour_offset 1` is the hour after the current hour.
- WebSocket loop ran a blocking network call on the event loop; now `asyncio.to_thread`.
- WebSocket `hotspots` entries had no `zone_name` (dashboard showed `undefined`).
- Random per-tick noise removed: live mode = real weather + fixed zone priors;
  DEMO mode = deterministic simulation (clock accelerated by `HEATSHIELD_SIM_SPEEDUP`).
- If the model is missing/unloadable the API now returns **503** instead of
  silently predicting a constant 50.
- `anthropic` calls have a 15 s timeout; fenced-JSON replies parsed correctly.

**Fixed (honesty / docs)**
- Docs said RandomForest R² 0.874; the saved model is **Ridge**. All docs, the
  dashboard KPI and status text now read the algorithm from the model metadata.
- Training data now covers one full seasonal cycle (365 days, 24,090 rows);
  the generator docstring finally matches the code.
- `train.py` records the **synthetic noise ceiling** R² (exact formula on the
  test targets) and the scikit-learn version; the dashboard's Model Performance
  page explains that R² near the ceiling = formula recovered, not real accuracy.
- Zone "risk explanation" is now model-driven: counterfactual re-prediction
  against the city-average zone priors (risk points), instead of an if/else
  template; the dashboard shows these per-zone drivers instead of the same
  global importance bars for every zone.
- Feature-importance wording changed from "measured" to "model-estimated";
  the importance method is stored in the metadata.
- Zone priors are explicitly labelled unverified in code, API and docs.

**Frontend**
- API/WS URL derived from where the page is served (`?api=` override);
  no hard-coded `localhost`. Dashboard is served by the backend at `/`.
- Fake `Math.random()` offline preview removed: when the backend is down a
  banner is shown and the socket reconnects automatically.
- Trend chart uses the server's persisted history (survives reloads).
- Server text is HTML-escaped before insertion.

**Hardening / deployment**
- CORS restricted by default (`ALLOWED_ORIGINS`), per-IP rate limit, WebSocket
  connection cap, optional `HEATSHIELD_API_KEY` for `/api/predict`, pydantic
  range validation on `/api/predict`.
- Dockerfile serves the dashboard, runs as non-root, has a healthcheck;
  `.dockerignore` added; model `.joblib` is committed (no longer git-ignored).
- Requirements use version ranges; the backend warns when the installed
  scikit-learn differs from the one that trained the model.
- Tests: 17 -> 44 (regressions for every bug above, live-weather path with a
  mocked Open-Meteo, rate limit, 503 behaviour, WebSocket).

---
## Earlier rounds (kept for history)

### Fixes (round 1)

1. **Map coverage/gaps**: Old `ZONE_LAYOUT` used hand-guessed SVG polygon
   points, disconnected from real coordinates -> visible gaps and wrong
   relative positions. Replaced with a runtime nearest-zone (Voronoi-style)
   grid fill computed from `ZONES_META`'s real lat/lon (mirrors
   `data/zones.py`). Verified: all 11 zones now appear with zero gaps
   across a 56x42 cell grid.

2. **Frozen header temperature / risk ring / "click a zone" stuck**: Caused
   by `new Chart(...)` throwing when Chart.js's CDN script hadn't finished
   loading yet (slow/blocked network) -- the exception silently aborted the
   rest of `applySnapshot()`/`selectZone()`, which is why KPI cards updated
   (they ran first) but the header, ring, and zone-details panel did not
   (they ran after the chart code). Fixed by: (a) reordering so all plain-DOM
   text updates happen before any chart code, (b) wrapping every
   `new Chart(...)` call in try/catch with a `typeof Chart === 'undefined'`
   guard, so a slow/blocked CDN degrades gracefully (charts just don't draw)
   instead of freezing the whole dashboard.

3. **Demo/offline fallback crash**: `startClientPreview()`'s `fakeTick()`
   still referenced the deleted `ZONE_LAYOUT` object, which would have
   produced zero zones (and NaN values) whenever the backend wasn't running.
   Fixed to source zones from the same `ZONES_META` list used by the real map.

### Fixes (round 2)

4. **Sidebar nav was fully decorative** (`<a>` tags with no click handlers,
   no `data-target`). Every item now does something real:
   - Heat Map / Hotspots / Zone Intelligence / AI Recommendations / Historical
     Analysis: smooth-scrolls to and flash-highlights that live card on
     Overview (no duplicate panels needed since they're already on-screen).
   - Forecast / Data Sources / Model Performance / Alerts / Settings: real
     dedicated sections. Forecast, Data Sources and Model Performance fetch
     live data from the backend and show an honest
     "Backend offline — cannot retrieve real X right now" message (never
     fake data) if the backend isn't running. Alerts applies real
     threshold logic (risk ≥ 71 High / ≥ 86 Extreme) to whatever zone data
     is currently on screen. Settings is explicitly labeled COMING SOON.

5. **Map upgraded to a real map**: replaced the abstract grid visualization
   with Leaflet.js + free OpenStreetMap tiles (genuine Moradabad street map,
   pan/zoom, real geography) — no API key required, unlike Google Maps'
   JS API which needs a billing-enabled key. Zone markers sit at their real
   lat/lon (same source as `data/zones.py`) and are colored/sized by live
   risk score; clicking a marker opens that zone's details exactly like
   before. If Leaflet's CDN fails to load, the app automatically falls back
   to the old grid-cell map so it's never blank.

### Fixes (round 3) — real weather API + dashboard cleanup

6. **Real weather, finally**: added `backend/services/weather.py`
   (Open-Meteo, free, no key). `air_temp`/`humidity`/`wind_speed` are now
   genuine current Moradabad readings instead of a synthetic diurnal curve,
   with an automatic, clearly-flagged fallback to simulation if the network
   is down. This is why the dashboard temperature will now actually track
   the real outside temperature instead of drifting to an unrelated number.
   `DATA_MODE` is derived live from whether this fetch is currently
   succeeding (see §4 above) instead of being a hardcoded `"DEMO"` string.

7. **Removed decorative/duplicate dashboard items** ("faltu features"):
   - Sidebar previously had 5 extra links (Heat Map, Hotspots, Zone
     Intelligence, AI Recommendations, Historical Analysis) that did nothing
     but scroll to a card already visible on the Overview page — removed;
     Overview still shows all of these cards together, just without
     redundant nav entries pointing at themselves.
   - **Alerts** section removed: it was a second, mostly-duplicate view of
     the same risk-threshold logic already shown by the Hotspots card on
     Overview.
   - **Settings** section removed: it was a static "COMING SOON" placeholder
     with no real functionality.
   - Sidebar now has exactly 4 real destinations: **Overview, Forecast,
     Model Performance, Data Sources** — each one does something the others
     don't.

8. **Fixed a real Data Sources bug**: the frontend's `loadDataSources()` was
   reading `s.source` / `s.detail` fields that the backend never sent (it
   sends `name` / `status` / `last_updated`) — so the Data Sources table
   rendered blank/undefined even when the backend responded correctly. Now
   reads the actual response shape and shows a real last-updated timestamp
   for the weather source.
