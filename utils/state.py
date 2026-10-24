"""Compose one consistent set of inventory and demand values for all pages."""
import time

import streamlit as st

from utils.inventory import (
    calculate_stock,
    fill_from_distance,
    inventory_status,
    is_valid_distance_calibration,
    reorder_point,
    suggested_order,
)
from utils.model import get_model_status, predict_demand
from utils.sensor import get_sensor_service, LIVE_SENSOR
from utils.simulation import get_simulated_reading


def estimate_inventory(sensor, capacity, container_height, simulated_distance, full_distance, empty_distance):
    """Choose a calibrated live reading or the simulated fallback."""
    calibration_valid = is_valid_distance_calibration(full_distance, empty_distance)
    live_available = sensor["mode"] == LIVE_SENSOR and sensor["reading"] is not None
    if live_available and calibration_valid:
        distance = sensor["reading"].distance_cm
        fill_percent = fill_from_distance(container_height, distance, full_distance, empty_distance)
        source = LIVE_SENSOR
        status = "Live sensor reading"
    else:
        simulated = get_simulated_reading(
            simulated_distance, container_height, capacity, full_distance, empty_distance
        )
        distance = simulated["distance_cm"]
        fill_percent = simulated["fill_percent"]
        source = "Simulation"
        status = (
            "Live distance received; invalid calibration means inventory remains simulated."
            if live_available and not calibration_valid else simulated["status"]
        )
    return {
        "distance_cm": distance,
        "fill_percent": fill_percent,
        "stock": calculate_stock(capacity, fill_percent),
        "inventory_source": source,
        "sensor_status": status,
        "calibration_valid": calibration_valid,
    }


def refresh_shared_data():
    """Refresh derived values from session controls and the latest service snapshot."""
    state = st.session_state
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    features = {
        "previous_day_demand": state.previous_day,
        "previous_week_demand": state.previous_week,
        "rolling_7_day_avg": state.rolling_avg,
        "day_of_week": weekdays.index(state.weekday),
    }
    prediction, prediction_error = predict_demand(features)

    sensor = get_sensor_service().snapshot()
    height = state.container_height
    capacity = state.capacity
    full_distance = state.valid_min_distance
    empty_distance = state.valid_max_distance
    inventory = estimate_inventory(
        sensor, capacity, height, state.distance_cm, full_distance, empty_distance
    )
    distance = inventory["distance_cm"]
    fill_percent = inventory["fill_percent"]
    stock = inventory["stock"]
    scenario_demand = (
        max(0.0, prediction * (1 + state.demand_change / 100))
        if prediction is not None else None
    )
    rop = reorder_point(scenario_demand, state.lead_time, state.safety_stock) if scenario_demand is not None else None
    data = {
        "capacity": capacity,
        "container_height": height,
        "valid_min_distance": full_distance,
        "valid_max_distance": empty_distance,
        "distance_cm": distance,
        "fill_percent": fill_percent,
        "stock": stock,
        "sensor_status": inventory["sensor_status"],
        "sensor": sensor,
        "sensor_mode": sensor["mode"],
        "sensor_state": sensor["state"],
        "inventory_source": inventory["inventory_source"],
        "sensor_reading_timestamp": sensor["reading"].timestamp if sensor["reading"] else None,
        "sensor_reading_age_seconds": sensor["reading_age_seconds"],
        "calibration_valid": inventory["calibration_valid"],
        "predicted_demand": prediction,
        "prediction_error": prediction_error,
        "scenario_demand": scenario_demand,
        "lead_time": state.lead_time,
        "safety_stock": state.safety_stock,
        "reorder_point": rop,
        "suggested_order": suggested_order(stock, rop) if rop is not None else None,
        "demand_change": state.demand_change,
        "features": features,
        "model_status": get_model_status(),
        "inventory_status": inventory_status(stock, fill_percent, rop),
    }
    state.app_data = data
    return data


@st.fragment(run_every=1.0)
def refresh_pages_when_sensor_changes():
    """Poll the shared service and rerun the full page when sensor state changes."""
    snapshot = get_sensor_service().snapshot()
    reading = snapshot["reading"]
    signature = (snapshot["state"], reading.timestamp if reading else None)
    previous = st.session_state.get("_sensor_render_signature")
    now = time.monotonic()
    last_refresh = st.session_state.get("_sensor_render_refresh_at", 0.0)
    if previous is None:
        st.session_state["_sensor_render_signature"] = signature
        st.session_state["_sensor_render_refresh_at"] = now
    elif signature != previous and now - last_refresh >= 0.8:
        st.session_state["_sensor_render_signature"] = signature
        st.session_state["_sensor_render_refresh_at"] = now
        st.rerun(scope="app")
