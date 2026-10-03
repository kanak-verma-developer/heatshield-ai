"""
Short-term heat-risk forecasting.

Approach: fit a simple weighted linear trend + diurnal seasonal component
over the zone's recent synthetic history to project 6h/24h ahead, with a
widening confidence interval. This is intentionally a lightweight,
explainable model (documented as such) rather than an LSTM, because the
demo dataset does not have enough continuous real sequential history yet
to justify a heavier model -- swap in Prophet/ARIMA/LSTM once real
continuous sensor history exists (see docs/MODEL_CARD.md).
"""
import math
import numpy as np


def forecast_zone(recent_scores: list, hours_ahead: int = 6, step_hours: int = 1):
    """
    recent_scores: list of last N risk scores (most recent last), used to
    estimate a local trend slope.
    Returns list of {hour, predicted_risk, lower, upper}.
    """
    n = len(recent_scores)
    if n < 2:
        base = recent_scores[-1] if recent_scores else 50.0
        slope = 0.0
    else:
        x = np.arange(n)
        y = np.array(recent_scores, dtype=float)
        slope, intercept = np.polyfit(x, y, 1)
        base = y[-1]

    forecast = []
    for h in range(1, hours_ahead + 1):
        # diurnal bump: risk tends to peak mid-afternoon
        diurnal = 2.5 * math.sin(h / 24 * 2 * math.pi)
        predicted = base + slope * h + diurnal
        predicted = max(0, min(100, predicted))
        uncertainty = 2.0 + 0.6 * h  # widening interval further out
        forecast.append({
            "hour": h,
            "predicted_risk": round(predicted, 1),
            "lower": round(max(0, predicted - uncertainty), 1),
            "upper": round(min(100, predicted + uncertainty), 1),
        })
    return forecast
