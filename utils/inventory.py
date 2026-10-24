"""Shared inventory and replenishment calculations."""
import math


def clamp(value, minimum, maximum):
    return max(minimum, min(float(value), maximum))


def is_valid_distance_calibration(full_distance_cm, empty_distance_cm):
    """Return whether calibration endpoints are finite and correctly ordered."""
    try:
        full_distance = float(full_distance_cm)
        empty_distance = float(empty_distance_cm)
    except (TypeError, ValueError, OverflowError):
        return False
    return (
        math.isfinite(full_distance)
        and math.isfinite(empty_distance)
        and full_distance >= 0.0
        and empty_distance > full_distance
    )


def fill_from_distance(container_height_cm, distance_cm, valid_min_cm=0.0, valid_max_cm=None):
    """Map a calibrated sensor-to-surface distance to an occupancy estimate.

    ``valid_min_cm`` is the calibrated target distance and ``valid_max_cm``
    is the empty-level baseline. Container height supplies the empty endpoint
    only when no explicit empty calibration is provided; it does not infer
    physical volume or package count.
    """
    height = max(0.1, float(container_height_cm))
    full_endpoint = valid_min_cm
    empty_endpoint = height if valid_max_cm is None else valid_max_cm
    if not is_valid_distance_calibration(full_endpoint, empty_endpoint):
        raise ValueError("Empty-level calibration must be greater than full-level calibration.")
    full_distance = float(full_endpoint)
    empty_distance = float(empty_endpoint)
    distance = float(distance_cm)
    if not math.isfinite(distance):
        raise ValueError("Measured distance must be a finite number.")
    distance = clamp(distance, full_distance, empty_distance)
    return clamp(
        100.0 * (empty_distance - distance) / (empty_distance - full_distance),
        0.0,
        100.0,
    )


def calculate_stock(capacity_units, fill_percent):
    return max(0.0, float(capacity_units)) * clamp(fill_percent, 0.0, 100.0) / 100.0


def reorder_point(daily_demand, lead_time_days, safety_stock_units):
    return max(0.0, float(daily_demand)) * max(0.0, float(lead_time_days)) + max(0.0, float(safety_stock_units))


def suggested_order(stock_units, reorder_point_units):
    return max(0, math.ceil(max(0.0, float(reorder_point_units)) - max(0.0, float(stock_units))))


def days_of_stock(stock_units, daily_demand):
    demand = float(daily_demand)
    return max(0.0, float(stock_units)) / demand if demand > 0 else None


def inventory_status(stock_units, fill_percent, reorder_point_units):
    if fill_percent <= 10 or stock_units <= 0:
        return "Critical"
    if reorder_point_units is not None and stock_units <= reorder_point_units:
        return "Reorder required"
    if fill_percent <= 30:
        return "Low"
    return "Healthy"
