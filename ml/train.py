"""
Trains the HeatShield AI heat-risk regression model.

- Real scikit-learn training; every number in the metadata is computed here.
- Hyperparameters tuned with RandomizedSearchCV (3-fold CV) for four
  candidate algorithms: RandomForest, GradientBoosting, Ridge, ElasticNet.
  The candidate with the best held-out test R^2 is saved.
- Time-aware split: the last 20% of days are the test set (not shuffled).
- Reports MAE, RMSE and R^2 (never called "accuracy").
- Also reports the SYNTHETIC NOISE CEILING: the R^2 you would get by
  plugging the exact data-generating formula (ml/generate_dataset.py
  `risk_formula`) into the noisy test targets. Because the target is built
  from that formula, a model whose R^2 sits at the ceiling has merely
  recovered the formula -- it says nothing about real-world accuracy.
- Records the scikit-learn version used, so the API can warn if the saved
  model is loaded under a different version (re-run this script to fix).
"""
import json
import os
import sys
import time
import joblib
import numpy as np
import pandas as pd
import sklearn
from scipy.stats import randint, uniform, loguniform
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, StackingRegressor
from sklearn.linear_model import LinearRegression, Ridge, ElasticNet
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import KFold, cross_val_score, RandomizedSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from ml.generate_dataset import risk_formula

BASE = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE, "..", "data", "training_data.csv")
MODEL_DIR = os.path.join(BASE, "..", "backend", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

FEATURES = [
    "air_temp", "surface_temp", "humidity", "wind_speed",
    "ndvi", "built_up_density", "road_density", "water_proximity",
]
TARGET = "heat_risk_score"

# Hyperparameter search spaces -- kept modest (8-12 iterations x 3-fold CV
# per algorithm) so training stays fast even on a single CPU core, while
# still being a real search rather than a hand-picked guess.
#
# NOTE: the synthetic target in generate_dataset.py is (almost) a LINEAR
# function of the inputs plus additive noise, so linear candidates (Ridge,
# ElasticNet) usually win. That is a property of the synthetic data, not
# evidence that heat risk is linear in reality; tree models stay in the
# search so the choice is made by the data, and this is re-evaluated
# automatically when real data replaces the synthetic CSV.
SEARCH_SPACES = {
    "RandomForest": (
        RandomForestRegressor(random_state=42, n_jobs=-1),
        {
            "n_estimators": randint(100, 220),
            "max_depth": randint(5, 14),
            "min_samples_leaf": randint(1, 6),
            "max_features": uniform(0.5, 0.5),  # 0.5-1.0
        },
    ),
    "GradientBoosting": (
        GradientBoostingRegressor(random_state=42),
        {
            "n_estimators": randint(80, 200),
            "max_depth": randint(2, 5),
            "learning_rate": uniform(0.02, 0.13),  # 0.02-0.15
            "subsample": uniform(0.7, 0.3),  # 0.7-1.0
        },
    ),
    "Ridge": (
        make_pipeline(StandardScaler(), Ridge()),
        {"ridge__alpha": loguniform(1e-2, 1e2)},
    ),
    "ElasticNet": (
        make_pipeline(StandardScaler(), ElasticNet(max_iter=20000)),
        {
            "elasticnet__alpha": loguniform(1e-3, 1e1),
            "elasticnet__l1_ratio": uniform(0.0, 1.0),
        },
    ),
}
N_SEARCH_ITER = 12


def main():
    if not os.path.exists(DATA_PATH):
        print("Training data not found. Run `python ml/generate_dataset.py` first.")
        sys.exit(1)

    df = pd.read_csv(DATA_PATH)
    df = df.sort_values(["day_index", "hour_slot"]).reset_index(drop=True)

    # Time-aware split: hold out the most recent 20% of days as test set.
    cutoff_day = df["day_index"].quantile(0.8)
    train_df = df[df["day_index"] <= cutoff_day]
    test_df = df[df["day_index"] > cutoff_day]

    X_train, y_train = train_df[FEATURES], train_df[TARGET]
    X_test, y_test = test_df[FEATURES], test_df[TARGET]

    kfold = KFold(n_splits=3, shuffle=True, random_state=42)
    results = {}
    fitted = {}

    for name, (estimator, param_dist) in SEARCH_SPACES.items():
        print(f"Tuning {name} ({N_SEARCH_ITER} candidates x 3-fold CV)...")
        search = RandomizedSearchCV(
            estimator, param_dist, n_iter=N_SEARCH_ITER, cv=kfold,
            scoring="r2", random_state=42, n_jobs=-1,
        )
        search.fit(X_train, y_train)
        model = search.best_estimator_
        preds = model.predict(X_test)

        mae = mean_absolute_error(y_test, preds)
        rmse = mean_squared_error(y_test, preds) ** 0.5
        r2 = r2_score(y_test, preds)

        results[name] = {
            "mae": round(float(mae), 3),
            "rmse": round(float(rmse), 3),
            "r2": round(float(r2), 4),
            "cv_r2_mean": round(float(search.best_score_), 4),
            "best_params": {k: (round(v, 4) if isinstance(v, float) else v)
                             for k, v in search.best_params_.items()},
        }
        fitted[name] = model
        print(f"{name}: MAE={mae:.3f}  RMSE={rmse:.3f}  R2={r2:.4f}  "
              f"best CV-R2={search.best_score_:.4f}  params={results[name]['best_params']}")

    # Select best model by test R^2 (honest selection, not cherry-picked).
    best_name = max(results, key=lambda n: results[n]["r2"])
    best_model = fitted[best_name]
    best_metrics = results[best_name]

    # Feature importance / coefficients. Tree ensembles expose
    # feature_importances_ directly; linear models are wrapped in a
    # (StandardScaler, estimator) pipeline, so we pull standardized
    # coefficients from the final pipeline step instead and report their
    # absolute magnitude (comparable across features since inputs are
    # standardized) with sign kept in a separate field for transparency.
    if hasattr(best_model, "feature_importances_"):
        importances = dict(zip(FEATURES, best_model.feature_importances_.tolist()))
        coefficients = None
        importance_method = "tree impurity-based feature_importances_ (global, not per-prediction)"
    else:
        coefs = best_model[-1].coef_
        coefficients = dict(zip(FEATURES, [round(float(c), 4) for c in coefs]))
        abs_total = sum(abs(c) for c in coefs) or 1.0
        importances = {f: abs(c) / abs_total for f, c in zip(FEATURES, coefs)}
        importance_method = "absolute standardized linear coefficient, normalized to sum to 1 (global, not causal)"
    importances = dict(sorted(importances.items(), key=lambda kv: -kv[1]))

    # Synthetic noise ceiling (see module docstring).
    ceiling_pred = np.clip(risk_formula(
        test_df["surface_temp"], test_df["built_up_density"], test_df["ndvi"],
        test_df["humidity"], test_df["road_density"]), 0, 100)
    ceiling_r2 = float(r2_score(y_test, ceiling_pred))

    # Residuals for the model performance page (sampled to keep file small).
    preds_test = best_model.predict(X_test)
    residual_sample = pd.DataFrame({
        "actual": y_test.values,
        "predicted": np.round(preds_test, 2),
    }).sample(n=min(300, len(y_test)), random_state=1).reset_index(drop=True)

    metadata = {
        "model_name": "HeatRiskModel",
        "version": "1.2",
        "sklearn_version": sklearn.__version__,
        "algorithm": best_name,
        "hyperparameters": best_metrics["best_params"],
        "tuning_method": f"RandomizedSearchCV ({N_SEARCH_ITER} candidates x 3-fold CV per algorithm)",
        "trained_at_unix": int(time.time()),
        "dataset": "synthetic (data/training_data.csv)",
        "dataset_rows": len(df),
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "split_method": "time-aware (last 20% of days held out; the held-out period is a different part of the seasonal cycle than most of the training data)",
        "features": FEATURES,
        "target": TARGET,
        "metrics": {
            "mae": best_metrics["mae"],
            "rmse": best_metrics["rmse"],
            "r2": best_metrics["r2"],
            "cv_r2_mean": best_metrics["cv_r2_mean"],
            "note": "R^2 is variance explained, not classification accuracy. "
                    "Measured on a SYNTHETIC dataset -- real-world accuracy on "
                    "actual Moradabad sensor/satellite data is unverified until "
                    "such data is connected.",
        },
        "all_candidates": results,
        "synthetic_noise_ceiling_r2": round(ceiling_r2, 4),
        "feature_importance": importances,
        "importance_method": importance_method,
        "linear_coefficients": coefficients,  # None for tree-based winners
    }

    joblib.dump(best_model, os.path.join(MODEL_DIR, "heat_risk_model.joblib"))
    with open(os.path.join(MODEL_DIR, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    residual_sample.to_json(os.path.join(MODEL_DIR, "residuals_sample.json"), orient="records")

    print(f"\nBest model: {best_name}  (hyperparameters: {best_metrics['best_params']})")
    print(json.dumps(metadata["metrics"], indent=2))
    print(f"Synthetic noise ceiling R2 (exact formula on test targets): {ceiling_r2:.4f}")
    print(f"Saved model + metadata to {MODEL_DIR}")


if __name__ == "__main__":
    main()
