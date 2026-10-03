"""
Generates a SYNTHETIC training dataset for the HeatShield AI heat-risk model.

Data honesty notice
--------------------
This is demo/synthetic data, not real Moradabad sensor or satellite data.
It is built from a physically-motivated formula (surface temp rises with
built-up density and falls with vegetation/water, etc.) plus random noise,
so a real ML pipeline has something realistic to fit. Every row is tagged
data_source="synthetic" in the CSV so nothing downstream can accidentally
present it as real. Swap this script's output for a real IMD/Sentinel-2/
NASA POWER-derived CSV (same column names) to make the whole system real
without touching the ML or API code.

Coverage: 365 days x 6 samples/day (every 4 hours) x 11 zones = 24,090 rows,
i.e. ONE FULL seasonal cycle, so the seasonal term in
`seasonal_air_temp` (period = 365 days) is actually covered. The diurnal
curve is a continuous sine (same functional form as the DEMO-mode
simulation in backend/services/state.py).

IMPORTANT (circularity): heat_risk_score is produced by `risk_formula`
below plus Gaussian noise, and the model is then trained to predict it
from the same inputs. High R^2 therefore only shows that the model can
recover that formula -- ml/train.py reports this "noise ceiling" next to
the model's R^2 so nobody mistakes it for real-world accuracy.
"""
import csv
import math
import random
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from data.zones import ZONES

random.seed(42)

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "training_data.csv")

N_DAYS = 365           # one full seasonal cycle (matches the 365-day period in seasonal_air_temp)
SAMPLES_PER_DAY = 6    # every 4 hours


def seasonal_air_temp(day_index, hour_of_day):
    """Base air temp: smooth seasonal curve (summer peak) + smooth diurnal
    sine curve (coolest ~5am, warmest ~4pm) -- same functional form as the
    live-fallback simulation in backend/services/state.py, so the model
    trains on physics consistent with what it sees at inference time."""
    season = 32 + 8 * math.sin(2 * math.pi * (day_index / 365.0) - 1.4)
    diurnal = 6 * math.sin((hour_of_day - 6) / 24 * 2 * math.pi)
    return season + diurnal


def risk_formula(lst, built_up, ndvi, humidity, road_density):
    """Noise-free synthetic heat-risk target (0-100 before clipping).
    Exposed so ml/train.py can compute the 'noise ceiling' R^2."""
    return (
        0.42 * (lst - 20) / 40 * 100
        + 0.24 * built_up * 100
        + 0.18 * (1 - ndvi) * 60
        - 0.09 * (humidity - 50) * 0.5
        + 0.07 * road_density * 40
    )


def make_row(zone, day_index, hour_of_day):
    air_temp = seasonal_air_temp(day_index, hour_of_day) + random.gauss(0, 1.1)

    built_up = min(1.0, max(0.0, zone["built_up_density"] + random.gauss(0, 0.03)))
    ndvi = min(0.9, max(0.02, zone["ndvi_base"] + random.gauss(0, 0.03)))
    road_density = min(1.0, max(0.0, zone["road_density"] + random.gauss(0, 0.03)))
    water_proximity = min(1.0, max(0.0, zone["water_proximity"] + random.gauss(0, 0.03)))
    humidity = max(10, min(90, 55 - 20 * (built_up - 0.5) + 15 * water_proximity + random.gauss(0, 4)))
    wind_speed = max(0.2, random.gauss(2.4, 0.9))

    # Land Surface Temperature: physically-motivated synthetic formula.
    lst = (
        air_temp
        + 9.0 * built_up
        - 7.0 * ndvi
        + 3.0 * road_density
        - 2.5 * water_proximity
        - 0.6 * wind_speed
        + random.gauss(0, 1.3)
    )

    # Heat risk score (0-100): weighted combination -> the ML model has to
    # (re)discover this mapping from the raw features, it is not told the formula.
    risk = risk_formula(lst, built_up, ndvi, humidity, road_density) + random.gauss(0, 3.5)
    risk = max(0, min(100, risk))

    return {
        "zone_id": zone["id"],
        "zone_name": zone["name"],
        "lat": zone["lat"],
        "lon": zone["lon"],
        "day_index": day_index,
        "hour_slot": hour_of_day,
        "air_temp": round(air_temp, 2),
        "surface_temp": round(lst, 2),
        "humidity": round(humidity, 1),
        "wind_speed": round(wind_speed, 2),
        "ndvi": round(ndvi, 3),
        "built_up_density": round(built_up, 3),
        "road_density": round(road_density, 3),
        "water_proximity": round(water_proximity, 3),
        "heat_risk_score": round(risk, 2),
        "data_source": "synthetic",
    }


def main():
    rows = []
    hour_step = 24 // SAMPLES_PER_DAY
    for day in range(N_DAYS):
        for slot in range(SAMPLES_PER_DAY):
            hour_of_day = slot * hour_step
            for zone in ZONES:
                rows.append(make_row(zone, day, hour_of_day))

    fieldnames = list(rows[0].keys())
    with open(OUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} synthetic rows -> {OUT_PATH}")


if __name__ == "__main__":
    main()
