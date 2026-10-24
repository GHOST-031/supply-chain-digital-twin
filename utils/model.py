"""Demand model loading, validation, and prediction."""
from pathlib import Path
import warnings

import joblib
import numpy as np
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "demand_model_v2.joblib"
MODEL_FEATURES = ("previous_day_demand", "previous_week_demand", "rolling_7_day_avg", "day_of_week")


@st.cache_resource(show_spinner=False)
def load_model():
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    # The project model was saved with an older sklearn version; preserve it and
    # surface compatibility information on the health page instead of hiding it.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model = joblib.load(MODEL_PATH)
    return model, [str(w.message) for w in caught]


def get_model_status():
    info = {"path": str(MODEL_PATH), "available": MODEL_PATH.is_file(), "loaded": False,
            "features": list(MODEL_FEATURES), "warnings": [], "error": None, "estimator": None}
    if not info["available"]:
        info["error"] = "demand_model_v2.joblib is missing."
        return info
    try:
        model, model_warnings = load_model()
        info.update(loaded=True, warnings=model_warnings,
                    features=list(getattr(model, "feature_names_in_", MODEL_FEATURES)),
                    estimator=type(model).__name__)
    except Exception as exc:
        info["error"] = f"Model could not be loaded: {exc}"
    return info


def predict_demand(values):
    """Predict from named, finite, non-negative demand features."""
    try:
        row = {name: float(values[name]) for name in MODEL_FEATURES}
        if not all(np.isfinite(v) for v in row.values()):
            raise ValueError("All model inputs must be finite numbers.")
        if any(row[name] < 0 for name in MODEL_FEATURES[:3]):
            raise ValueError("Demand inputs cannot be negative.")
        if row["day_of_week"] not in range(7):
            raise ValueError("Day of week must be an integer from 0 to 6.")
        model, _ = load_model()
        frame = pd.DataFrame([[row[name] for name in MODEL_FEATURES]], columns=MODEL_FEATURES)
        prediction = float(model.predict(frame)[0])
        if not np.isfinite(prediction):
            raise ValueError("The model returned a non-finite prediction.")
        return max(0.0, prediction), None
    except Exception as exc:
        return None, str(exc)
