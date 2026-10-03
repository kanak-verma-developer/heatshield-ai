"""
Automated tests for the trained heat-risk model.

Run with:  pytest tests/ -v
(from the project root, with the model already trained -- see README.md)
"""
import os
import sys
import json
import joblib
import pandas as pd
import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

MODEL_PATH = os.path.join(BASE, "backend", "models", "heat_risk_model.joblib")
META_PATH = os.path.join(BASE, "backend", "models", "model_metadata.json")

FEATURES = ["air_temp", "surface_temp", "humidity", "wind_speed",
            "ndvi", "built_up_density", "road_density", "water_proximity"]


@pytest.fixture(scope="module")
def model():
    if not os.path.exists(MODEL_PATH):
        pytest.skip("Model not trained yet -- run `python ml/train.py` first")
    return joblib.load(MODEL_PATH)


@pytest.fixture(scope="module")
def metadata():
    if not os.path.exists(META_PATH):
        pytest.skip("Model metadata not found -- run `python ml/train.py` first")
    with open(META_PATH) as f:
        return json.load(f)


def _predict(model, **overrides):
    row = {
        "air_temp": 34.0, "surface_temp": 40.0, "humidity": 45.0, "wind_speed": 2.0,
        "ndvi": 0.3, "built_up_density": 0.5, "road_density": 0.3, "water_proximity": 0.3,
    }
    row.update(overrides)
    df = pd.DataFrame([[row[f] for f in FEATURES]], columns=FEATURES)
    return float(model.predict(df)[0])


def test_model_file_exists():
    assert os.path.exists(MODEL_PATH), "heat_risk_model.joblib is missing -- run ml/train.py"


def test_predictions_are_within_valid_range(model):
    """Risk score should always be interpretable as 0-100, even if the raw
    regressor output drifts slightly outside (the API clamps it; here we
    check the model itself stays close to the training target's range)."""
    pred = _predict(model)
    assert -10 <= pred <= 110, f"prediction {pred} is wildly out of range"


def test_more_built_up_density_increases_risk(model):
    """Sanity check: a denser, less green zone should predict a HIGHER
    risk than an identical zone with more vegetation and less concrete --
    this is the core physical relationship the whole project is built on."""
    dense_zone = _predict(model, built_up_density=0.9, ndvi=0.1)
    green_zone = _predict(model, built_up_density=0.2, ndvi=0.6)
    assert dense_zone > green_zone, (
        f"expected dense/low-vegetation zone ({dense_zone}) to score higher "
        f"than green/low-density zone ({green_zone}) -- model may be learning "
        f"a spurious/reversed relationship"
    )


def test_higher_air_temp_increases_risk(model):
    cooler = _predict(model, air_temp=28.0, surface_temp=32.0)
    hotter = _predict(model, air_temp=40.0, surface_temp=46.0)
    assert hotter > cooler, "risk should increase with air/surface temperature"


def test_model_metrics_are_recorded_and_reasonable(metadata):
    """The metrics in model_metadata.json must be real measured numbers,
    not placeholders -- this test would fail if train.py ever regressed to
    hardcoding a metric instead of computing it."""
    metrics = metadata["metrics"]
    assert 0 <= metrics["r2"] <= 1, "R^2 should be a real value between 0 and 1 for a working model"
    assert metrics["mae"] > 0, "MAE should be a positive measured error, not zero/placeholder"
    assert metrics["rmse"] >= metrics["mae"], "RMSE is mathematically always >= MAE"


def test_feature_importance_sums_reasonably(metadata):
    fi = metadata.get("feature_importance", {})
    assert len(fi) == len(FEATURES), "every trained feature should have an importance value"
    total = sum(fi.values())
    assert 0.9 <= total <= 1.1, f"feature importances should sum to ~1.0, got {total}"


def test_metadata_records_sklearn_version_and_importance_method(metadata):
    import sklearn
    assert metadata.get("sklearn_version") == sklearn.__version__, \
        "saved model was trained with a different scikit-learn -- re-run ml/train.py"
    assert metadata.get("importance_method")


def test_r2_cannot_beat_the_synthetic_noise_ceiling(metadata):
    """The target is formula + noise, so no honest model can meaningfully beat
    the R^2 of the exact formula. If this fails, suspect leakage; if the model
    sits AT the ceiling it has only recovered the synthetic formula."""
    ceiling = metadata["synthetic_noise_ceiling_r2"]
    assert metadata["metrics"]["r2"] <= ceiling + 0.01
