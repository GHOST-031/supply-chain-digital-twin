"""Reproducible demo data. Nothing in this module represents live hardware."""
import numpy as np
import pandas as pd

from utils.inventory import fill_from_distance, is_valid_distance_calibration


def get_simulated_reading(distance_cm, container_height_cm, capacity_units, valid_min_cm=0.0, valid_max_cm=None):
    height = max(0.1, float(container_height_cm))
    low = valid_min_cm
    high = height if valid_max_cm is None else valid_max_cm
    # Invalid or overlapping calibration ranges fall back to physical container bounds.
    calibration_valid = is_valid_distance_calibration(low, high)
    if not calibration_valid:
        low, high = 0.0, height
    else:
        low = float(low)
        high = float(high)
    bounded_distance = min(max(float(distance_cm), low), high)
    fill = fill_from_distance(height, bounded_distance, low, high)
    return {"distance_cm": bounded_distance, "fill_percent": fill,
            "stock_units": max(0.0, float(capacity_units)) * fill / 100.0,
            "mode": "Simulation",
            "status": "Simulated reading" if calibration_valid else "Simulated reading; invalid calibration fell back to container bounds",
            "calibration_valid": calibration_valid}


def synthetic_history(days=30, seed=17):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=days, freq="D")
    weekday = dates.dayofweek.to_numpy()
    pattern = np.array([19.5, 20.2, 21.0, 22.4, 24.1, 17.8, 16.2])[weekday]
    trend = np.linspace(-1.2, 1.2, days)
    demand = np.maximum(0, pattern + trend + rng.normal(0, 2.0, days))
    return pd.DataFrame({"date": dates, "demand_units": demand})


def synthetic_inventory_history(current_stock, capacity, days=14, seed=31):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=days, freq="D")
    capacity = max(0.0, float(capacity))
    # Build a plausible demonstration trend ending at the current simulated estimate.
    start = min(capacity, max(0.0, float(current_stock) + days * 1.2))
    values = np.linspace(start, max(0.0, float(current_stock)), days)
    if days > 2:
        values[1:-1] += rng.normal(0, max(0.1, capacity * 0.018), days - 2)
    values = np.clip(values, 0, capacity)
    values[-1] = min(capacity, max(0.0, float(current_stock)))
    return pd.DataFrame({"date": dates, "stock_units": values})
