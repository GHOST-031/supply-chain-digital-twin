# Supply Chain Digital Twin

Supply Chain Digital Twin is a Streamlit application for exploring inventory status and replenishment planning. It combines calibrated ultrasonic distance estimates, a preserved demand model, and shared planning calculations across six dashboard pages. Sensor readings can be simulated or received over an optional serial connection. The project also includes firmware, synthetic-data evaluation assets, and documentation for the application and hardware.

## Key features

- Six-page dashboard for executive overview, inventory, demand forecasting, scenario analysis, replenishment, and system health.
- Calibrated fill/occupancy estimates and capacity-scaled inventory units, with simulation available when verified live readings are unavailable.
- V2 demand predictions using the configured demand inputs, alongside separate synthetic demonstration histories.
- Shared demand, lead-time, safety-stock, reorder-point, and suggested-order calculations.
- Hypothetical scenario comparisons and downloadable replenishment recommendation CSV.
- Optional ESP8266/HC-SR04 serial integration with input validation and fallback to simulation after stale readings or disconnection.

## Technology stack

- Python and Streamlit
- pandas, NumPy, Plotly, joblib, and scikit-learn
- pyserial for optional serial sensor communication
- Arduino IDE and ESP8266 firmware

## Getting started

From the project root, create and activate a virtual environment, install the project dependencies, and start Streamlit:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

## Project structure

```text
.
├── README.md
├── app.py                  # Streamlit entry point and shared controls
├── pages/                  # Six dashboard pages
├── utils/                  # Model, sensor, inventory, and state helpers
├── firmware/               # Existing ESP8266 sensor sketch
├── hardware/               # Hardware subsystem documentation
├── training/               # Synthetic dataset and model evaluation guide
├── docs/                   # Project, UI, formula, demo, and verification guides
├── tests/                  # Unit and Streamlit AppTest coverage
├── demand_model.joblib     # V1 demand model
├── demand_model_v2.joblib  # V2 demand model used by the app
├── requirements.txt
└── SENSOR_SETUP.md
```

## Documentation

### Project and dashboard

- [Project-wide A-to-Z audit](docs/PROJECT_A_TO_Z_AUDIT.md) — architecture, implementation findings, and evidence boundaries.
- [UI element inventory](docs/UI_ELEMENT_INVENTORY.md) — dashboard elements and interactions by page.
- [KPI and formula reference](docs/KPI_AND_FORMULA_REFERENCE.md) — shared metrics and calculation definitions.
- [Demo and viva guide](docs/DEMO_AND_VIVA_GUIDE.md) — demonstration flow and technical discussion notes.
- [Test and verification report](docs/TEST_AND_VERIFICATION_REPORT.md) — automated checks and their scope.
- [Unverified items and gaps](docs/UNVERIFIED_ITEMS_AND_GAPS.md) — remaining evidence and manual verification needs.

### Sensor and hardware

- [Sensor setup](SENSOR_SETUP.md) — optional serial sensor setup, calibration, and simulation behavior.
- [Hardware README](hardware/README.md) — component specifications and firmware behavior, including the difference between the supplied reference sketch and the preserved repository sketch.

### Training assets

- [Training README](training/README.md) — synthetic dataset regeneration and evaluation instructions.

## Demand models

The repository preserves `demand_model.joblib` (V1) and `demand_model_v2.joblib` (V2). [`utils/model.py`](utils/model.py) loads V2 for dashboard predictions. See the [training documentation](training/README.md) for dataset and evaluation details.

## Hardware integration status

The application supports optional ESP8266/HC-SR04 readings over serial and remains usable in simulation mode. Live readings are used for inventory estimates only after a recent, validated measurement and valid calibration are available. The firmware communicates over serial; the project does not claim Wi-Fi sensor transmission or verified physical measurements. See the [hardware documentation](hardware/README.md) and [sensor setup guide](SENSOR_SETUP.md) for integration details and remaining verification limits.
