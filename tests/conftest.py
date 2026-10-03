"""Shared test setup: isolated DB, no real network, rate limiter off."""
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

# Must be set BEFORE backend modules are imported.
os.environ["HEATSHIELD_DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test_history.db")
os.environ["HEATSHIELD_RATE_LIMIT_PER_MIN"] = "0"
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ.pop("HEATSHIELD_API_KEY", None)

import pytest  # noqa: E402

MODEL_PATH = os.path.join(BASE, "backend", "models", "heat_risk_model.joblib")


def pytest_collection_modifyitems(config, items):
    if not os.path.exists(MODEL_PATH):
        skip = pytest.mark.skip(reason="Model not trained yet -- run `python ml/train.py` first")
        for item in items:
            item.add_marker(skip)


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload, self.status_code = payload, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def fake_open_meteo(url, params=None, timeout=None, calls=None):
    if calls is not None:
        calls.append(params)
    if params and "current" in params:
        return FakeResponse({"current": {"temperature_2m": 41.0, "relative_humidity_2m": 20.0,
                                         "wind_speed_10m": 7.2}})   # 7.2 km/h = 2.0 m/s
    n = params.get("forecast_hours", 49)
    return FakeResponse({"hourly": {
        "time": [f"t{i}" for i in range(n)],
        "temperature_2m": [30.0 + i for i in range(n)],          # index i -> 30 + i degC
        "relative_humidity_2m": [40.0] * n,
        "wind_speed_10m": [10.8] * n,                             # 3.0 m/s
    }})


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Every test starts with Open-Meteo unreachable (DEMO mode) and empty weather caches."""
    import requests
    from backend.services import weather

    def _down(*a, **k):
        raise requests.ConnectionError("network disabled in tests")

    monkeypatch.setattr(weather.requests, "get", _down)
    for cache in (weather._cache, weather._forecast_cache):
        cache.update({"data": None, "fetched_at": 0, "last_attempt": 0})
    from backend.services.state import state
    import backend.services.recommendations as rec
    state._snapshot = None
    state.last_forecast_method = None
    rec._llm_state.update(provider=None, last_ok=None, last_error=None, ts=None)
    yield
    state._snapshot = None
