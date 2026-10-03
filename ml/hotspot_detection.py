"""
Hotspot detection.

IMPROVEMENT (this version): pure z-score anomaly detection has a real blind
spot -- during a genuine city-wide heatwave, EVERY zone's risk score rises
together, so no single zone looks statistically anomalous relative to its
peers (z-scores all stay near 0) even though the actual danger is severe.
A hotspot detector that only measures "hotter than its neighbours right
now" would silently report zero hotspots during the exact scenario this
whole project exists to catch.

Fix: a zone is now flagged as a hotspot if EITHER is true:
  (a) it's a statistical outlier relative to the rest of the city right now
      (z-score >= z_threshold) -- catches "this one zone is unusually bad
      today", useful for targeting a specific intervention.
  (b) its absolute risk score is >= 71 ("Very High"/"Extreme" on the map's
      own legend) -- catches "this zone is dangerous in absolute terms",
      which stays true even in a city-wide event where nothing looks
      relatively anomalous.
Severity is then the more serious of the two signals, so a zone that's
both a relative outlier AND in absolute danger is never under-reported.
"""
import numpy as np

_SEVERITY_RANK = {"MODERATE": 1, "HIGH": 2, "CRITICAL": 3, "EXTREME": 4}


def _severity_from_zscore(z: float) -> str:
    if z >= 2.5:
        return "CRITICAL"
    if z >= 2.0:
        return "HIGH"
    return "MODERATE"


def _severity_from_absolute_score(score: float) -> str:
    """Matches the dashboard's own map legend buckets (0-25 Low, 26-50
    Moderate, 51-70 High, 71-85 Very High/CRITICAL, 86-100 Extreme) so the
    hotspot list and the map colors never disagree with each other."""
    if score >= 86:
        return "EXTREME"
    if score >= 71:
        return "CRITICAL"
    return "MODERATE"


def detect_hotspots(zone_scores: dict, z_threshold: float = 1.5, absolute_threshold: float = 71.0):
    """
    zone_scores: {zone_id: risk_score}
    returns (hotspots, citywide_event):
      hotspots -- list of dicts sorted by risk score (desc) for zones that
      are either a relative statistical outlier OR in absolute danger (see
      module docstring). Each entry reports both signals so the reason is
      transparent, not just a single opaque number.
      citywide_event -- True if literally every zone is at/above the
      absolute danger threshold (i.e. an actual city-wide heatwave, not
      just one bad zone).
    """
    ids = list(zone_scores.keys())
    values = np.array([zone_scores[i] for i in ids], dtype=float)

    mean = values.mean()
    std = values.std() if values.std() > 1e-6 else 1e-6
    z_scores = (values - mean) / std
    citywide_event = bool(np.all(values >= absolute_threshold))

    hotspots = []
    for zid, score, z in zip(ids, values, z_scores):
        is_relative_outlier = z >= z_threshold
        is_absolute_danger = score >= absolute_threshold
        if not (is_relative_outlier or is_absolute_danger):
            continue

        candidates = []
        if is_relative_outlier:
            candidates.append(_severity_from_zscore(z))
        if is_absolute_danger:
            candidates.append(_severity_from_absolute_score(score))
        severity = max(candidates, key=lambda s: _SEVERITY_RANK[s])

        hotspots.append({
            "zone_id": zid,
            "risk_score": round(float(score), 2),
            "anomaly_score": round(float(z), 2),
            "severity": severity,
            "trigger": (
                "both" if (is_relative_outlier and is_absolute_danger) else
                "relative_outlier" if is_relative_outlier else
                "absolute_danger"
            ),
        })

    hotspots.sort(key=lambda h: (-h["risk_score"], -h["anomaly_score"]))
    return hotspots, citywide_event
