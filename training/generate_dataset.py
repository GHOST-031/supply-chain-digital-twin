"""Recreate the synthetic demand data from training/original/Untitled0.ipynb.

This reproduces the notebook's NumPy seed, 365 generated days, demand formula,
lag features, rolling window, row drop, and day-of-week definition.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "training" / "synthetic_demand.csv"


def generate_dataset() -> pd.DataFrame:
    """Return the notebook dataset, including the later V2 weekday feature."""
    np.random.seed(42)
    days = np.arange(365)

    trend = 20 + 0.02 * days
    weekly_pattern = 3 * np.sin(2 * np.pi * days / 7)
    seasonality = 4 * np.sin(2 * np.pi * days / 30)
    noise = np.random.normal(0, 2, 365)
    demand = np.maximum(
        1, np.round(trend + weekly_pattern + seasonality + noise)
    ).astype(int)

    data = pd.DataFrame({"day": days + 1, "demand": demand})
    data["previous_day_demand"] = data["demand"].shift(1)
    data["previous_week_demand"] = data["demand"].shift(7)
    data["rolling_7_day_avg"] = data["demand"].shift(1).rolling(7).mean()
    data = data.dropna().reset_index(drop=True)
    data["day_of_week"] = (data["day"] - 1) % 7
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT,
        help=f"CSV output path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    data = generate_dataset()
    data.to_csv(output, index=False)
    print(f"Exported {len(data)} rows and {len(data.columns)} columns to {output}")


if __name__ == "__main__":
    main()
