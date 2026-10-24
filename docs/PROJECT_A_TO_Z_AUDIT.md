# Supply Chain Digital Twin: Project-Wide Audit

**Audit date:** 2026-10-23  
**Scope:** source, data, model artifacts, tests, documentation, and firmware in this workspace. The initial audit was read-only; a later targeted follow-up changed only the listed application, test, and documentation files. Firmware, dataset, dependencies, and model artifacts were not changed.  
**Evidence labels:** *Source inspected* means traced in code; *Tested* means an executed automated check; *AppTest* means Streamlit's Python test harness, not a browser; *Not verified* means no hardware or real browser evidence.

## Executive summary

The project is a six-page Streamlit application backed by a cached V2 linear regression model, a single process-wide optional serial reader, shared session-state calculations, synthetic demonstration histories, and a deterministic synthetic training/evaluation dataset. The existing tests pass. The current CSV reproduces byte-independent generated values in memory, and evaluating both existing model files on the existing chronological split reproduces all three notebook metrics when rounded to two decimals.

The supplied physical setup is **side-mounted**. The initial audit found stale top-mounted descriptions; the targeted follow-up updated the active UI, utility docstring, setup guide, and workflow text. The 2.6 cm endpoint remains a calibrated target, not evidence that the bin is physically full. The estimate is a one-beam, arrangement-specific distance index scaled by configured capacity, not measured volume or an exact package count.

The follow-up keeps the existing calibration math and makes the container-height control's fallback-only role explicit; separates scenario demand and inventory charts by units; and labels the fixed MAE values as notebook-reported benchmarks rather than runtime evaluation. No browser or physical sensor validation was performed.

## Project inventory

Paths are relative to the project root. “Tests” refers to the existing automated suite unless stated otherwise.

| File | Purpose | Imported/used by | Important functions/classes | Tests covering it | Verification status |
|---|---|---|---|---|---|
| `app.py` | Entry point, wide layout, shared controls, sensor sidebar, native navigation | `streamlit run app.py` | `render_sensor_controls`; six `st.Page` entries | AppTest all pages; test suite indirectly uses state/utilities | Source inspected; AppTest rendered |
| `pages/1_Executive_Overview.py` | Overview KPIs, health alerts, demo trends | Navigation | page script; synthetic history helpers | AppTest render only | Source inspected; AppTest rendered |
| `pages/2_Inventory_Digital_Twin.py` | Capacity, distance, calibrated occupancy, estimated stock, demo inventory history | Navigation | page script | Calibration/inventory tests; AppTest render | Tested calculations; page rendered |
| `pages/3_AI_Demand_Forecast.py` | V2 prediction, synthetic chart, weekday mean, fixed notebook-reported benchmark comparison | Navigation | page script | Model inference test; AppTest render/disclosure regression | Metric rerun; page rendered |
| `pages/4_Scenario_Simulator.py` | Form-based hypothetical demand and inventory scenarios with separate unit-labelled charts | Navigation | page script | Scenario chart regression; five parameters changed with AppTest | AppTest interactions verified |
| `pages/5_Replenishment_Alerts.py` | Planning recommendation, table, CSV download button | Navigation | page script | Reorder functions tested; AppTest render | Recommendation source inspected; button rendered, transfer not browser-tested |
| `pages/6_System_Health.py` | Sensor/model/data status and workflow explanation | Navigation | page script | Model/sensor tests; AppTest render | Source inspected; page rendered |
| `utils/__init__.py` | Package marker | Python imports | none | none | Inspected; no logic |
| `utils/inventory.py` | Shared calibration, stock, reorder and status formulas | State, simulation, pages 1/4 | `fill_from_distance`, `calculate_stock`, `reorder_point`, `suggested_order`, `days_of_stock`, `inventory_status` | Calibration, inventory/reorder regression tests | Source and tests verified |
| `utils/model.py` | V2 model loading, status, feature validation and inference | Shared state, health page | `load_model`, `get_model_status`, `predict_demand` | Existing demand prediction test | Loaded V2; current sklearn warning list empty |
| `utils/sensor.py` | Port discovery, parsing, threaded serial service, state transitions and cleanup | `app.py`, shared state | `parse_distance_line`, `SensorService`, `get_sensor_service` | Mock serial parsing/service tests | Mock-tested; no physical port opened |
| `utils/simulation.py` | Simulated reading and reproducible visual histories | Shared state and pages 1–3 | `get_simulated_reading`, `synthetic_history`, `synthetic_inventory_history` | Invalid calibration fallback test; page renders | Source inspected; simulation calculations tested in suite |
| `utils/state.py` | Shared calculation assembly in `st.session_state.app_data` | Entry point and all pages | `estimate_inventory`, `refresh_shared_data`, `refresh_pages_when_sensor_changes` | Inventory/model regression tests; AppTest | Source inspected; app pages rendered |
| `utils/ui.py` | Shared colors, header/data helpers, empty-chart helper | All pages | `page_header`, `shared_data`, `empty_chart` | None directly | Source inspected; `empty_chart` has no current caller |
| `requirements.txt` | Runtime dependency constraints | Environment setup | Streamlit, pandas, NumPy, Plotly, joblib, sklearn, pyserial | Environment check | Installed versions inspected; no installation performed |
| `SENSOR_SETUP.md` | macOS setup, firmware, serial and calibration directions | Human setup | none | none | Read; calibration wording is partly outdated (see findings) |
| `firmware/esp8266_hcsr04.ino` | ESP8266 + HC-SR04 sample firmware | Arduino IDE upload, not imported by Python | `setup`, `loop` | None; hardware needed | Source inspected only; no compile/upload/physical test |
| `tests/__init__.py` | Test package marker | unittest discovery | none | n/a | Read |
| `tests/test_sensor.py` | 23 unit tests for parsing, mocked serial service, calibration, stock/replenishment, and model inference | `python -m unittest discover -s tests -v` | `FakeSerial`; three test classes | This is the suite | 23 tests passed |
| `training/README.md` | Reproducible dataset/evaluation instructions | Human workflow | none | none | Read; commands/source cross-checked |
| `training/generate_dataset.py` | Recreates deterministic notebook-derived synthetic dataset | Optional CLI; not app startup | `generate_dataset`, `main` | No dedicated automated test | In-memory result exactly equalled existing CSV; script was not run because it writes the CSV |
| `training/evaluate_models.py` | Loads V1/V2 artifacts and evaluates fixed chronological holdout without fitting/saving | Optional CLI; not app startup | `evaluate`, `main` | Executed directly | Exit 0; metrics reproduced to 2 decimals |
| `training/synthetic_demand.csv` | 358-row synthetic training/evaluation data | Evaluator; generated by script | columns described below | Evaluator run | Schema and quality inspected; generator-equivalent DataFrame matched |
| `training/original/Untitled0.ipynb` | Original Colab training/evaluation notebook copy | Reference only; not imported at runtime | 9 notebook cells | Not run as notebook | JSON/source/output cells inspected |
| `demand_model.joblib` | Preserved V1 `LinearRegression`, 3 features | Evaluation script only | sklearn estimator | Evaluation script | Loaded/evaluated; SHA-256 recorded below |
| `demand_model_v2.joblib` | Preserved V2 `LinearRegression`, 4 features; production app model | `utils/model.py`, evaluator | sklearn estimator | Inference test, evaluator, AppTest | Loaded/evaluated; SHA-256 recorded below |
| `backups/app.py.before_upgrade` | Historical app snapshot | No runtime import found | snapshot source | none | Listed; not line-by-line audited as live code |
| `backups/sensor-integration-before/1_Executive_Overview.py` | Historical page snapshot | No runtime import found | snapshot | none | Snapshot only; not line-by-line audited |
| `backups/sensor-integration-before/2_Inventory_Digital_Twin.py` | Historical page snapshot | No runtime import found | snapshot | none | Snapshot only; not line-by-line audited |
| `backups/sensor-integration-before/3_AI_Demand_Forecast.py` | Historical page snapshot | No runtime import found | snapshot | none | Snapshot only; not line-by-line audited |
| `backups/sensor-integration-before/4_Scenario_Simulator.py` | Historical page snapshot | No runtime import found | snapshot | none | Snapshot only; not line-by-line audited |
| `backups/sensor-integration-before/5_Replenishment_Alerts.py` | Historical page snapshot | No runtime import found | snapshot | none | Snapshot only; not line-by-line audited |
| `backups/sensor-integration-before/6_System_Health.py` | Historical page snapshot | No runtime import found | snapshot | none | Snapshot only; not line-by-line audited |
| `backups/sensor-integration-before/__init__.py` | Historical package marker | No runtime import found | none | none | Read/listed; snapshot only |
| `backups/sensor-integration-before/inventory.py` | Historical inventory utility snapshot | No runtime import found | snapshot | none | Snapshot only; not line-by-line audited |
| `backups/sensor-integration-before/model.py` | Historical model utility snapshot | No runtime import found | snapshot | none | Snapshot only; not line-by-line audited |
| `backups/sensor-integration-before/sensor.py` | Historical sensor utility snapshot | No runtime import found | snapshot | none | Snapshot only; not line-by-line audited |
| `backups/sensor-integration-before/simulation.py` | Historical simulation utility snapshot | No runtime import found | snapshot | none | Snapshot only; not line-by-line audited |
| `backups/sensor-integration-before/ui.py` | Historical UI utility snapshot | No runtime import found | snapshot | none | Snapshot only; not line-by-line audited |
| `backups/sensor-integration-before/demand_model_v2.joblib` | Historical copy of V2 artifact | No runtime import found | serialized estimator | none | Snapshot exists; not evaluated |

Generated `__pycache__/*.pyc` files were present, are not source inputs, and were excluded from the source inventory. `.venv` was used to query installed packages and run checks; vendor files were not inventoried line-by-line. There is no Git repository metadata in the project root, so `git status`/diff-based change tracking is unavailable. No existing `docs/` directory was present at inspection time.

## Entry flow and page order

`streamlit run app.py` configures a wide Streamlit page, installs a small static CSS style block, renders shared planning controls and one shared sensor-status/control fragment, registers six native `st.Page` entries in the requested order, refreshes derived data, and runs the selected page. `refresh_shared_data()` writes the current calculated dictionary to session state. Each page calls `refresh_pages_when_sensor_changes()` so a new sensor state/reading can trigger a throttled app rerun.

The app does not start model training, use an external API, create a database, or persist sensor history. Serial access is process-wide through a cached `SensorService`; planning controls and derived `app_data` are per Streamlit session.

## Data, model, and environment

### Dataset

`training/synthetic_demand.csv` has 358 rows and columns `day`, `demand`, `previous_day_demand`, `previous_week_demand`, `rolling_7_day_avg`, and `day_of_week`. Types are int64 for day/demand/day-of-week and float64 for the lag/rolling features. The audit observed zero missing values, zero duplicate rows, and demand min/max of 12/34 units. These are generated demonstration values, not sales observations.

`generate_dataset()` was called in memory and its DataFrame compared with the existing CSV: exact DataFrame equality was `True`. The write-capable CLI was not run, so the dataset was not overwritten.

### Model artifacts

| Artifact | Estimator | Features in stored order | SHA-256 during audit |
|---|---|---|---|
| `demand_model.joblib` | `LinearRegression`, V1 | `previous_day_demand`, `previous_week_demand`, `rolling_7_day_avg` | `5fd83cf96e32fc914262ffbed5f35f538f5fbd421fe832fe206d128405b90105` |
| `demand_model_v2.joblib` | `LinearRegression`, V2 | V1 features plus `day_of_week` | `943ecc0c522dfdac82c838d5ba4042ce4339d5e9e16b4e6372ebf04d4c817889` |

`utils/model.py` loads only V2 for production. `training/evaluate_models.py` loads both existing artifacts and does not fit or save. Hashes were recorded before and after evaluation and matched. Current model environment reports Python 3.12.0, Streamlit 1.65.0, pandas 3.0.6, NumPy 2.5.4, scikit-learn 1.6.1, joblib 1.6.0, and Plotly 7.1.0. Requirements pin scikit-learn 1.6.1; `get_model_status()` loaded V2 and reported no compatibility warnings in this environment.

### Notebook methodology and reproduced metrics

The notebook sets NumPy seed 42, creates 365 days with trend `20 + 0.02 * day_index`, weekly sine component `3*sin(2πd/7)`, monthly sine component `4*sin(2πd/30)`, and Normal(0,2) noise. It rounds, floors at one, shifts target by 1 and 7 days, computes a prior-seven-observation average, drops initial missing rows, then defines weekday `(day - 1) % 7`. Both notebook versions split the 358 rows at `int(358 * .8) = 286`, preserving chronology. The previous-day baseline predicts with the held-out previous-day feature.

The evaluator produced 286 train / 72 test rows and these model-artifact results:

| Measure | Measured MAE | Notebook/UI reported | Measured minus reported | Rounded reproduction |
|---|---:|---:|---:|---:|
| V1 | 2.2236285197 | 2.22 | +0.0036285197 | 2.22 |
| V2 | 2.0868998601 | 2.09 | -0.0031001399 | 2.09 |
| Previous-day baseline | 2.3055555556 | 2.31 | -0.0044444444 | 2.31 |

All are synthetic-data benchmark errors in units/day. They do not establish warehouse performance. The holdout uses true lagged values available up to each evaluated point; this is a one-step-ahead style evaluation, not a long open-loop multi-day forecast.

## Pages and shared data flow

1. **Executive Overview** reads `app_data`, renders current stock, base prediction, reorder point, order, days of stock, status, and generated demo trends.
2. **Inventory Digital Twin** reads the same stock/fill/distance/source values and adds a simulated history ending at current estimated stock.
3. **AI Demand Forecast** reads the shared V2 prediction and demand adjustment; its history and weekday shape come from a separate deterministic demo generator, while fixed notebook-reported benchmark MAEs are distinguished from evaluation recomputed by the separate script.
4. **Scenario Simulator** uses current shared values as baseline, then form-local hypothetical demand percentage, lead time, capacity, inventory percentage, and safety stock.
5. **Replenishment & Alerts** uses shared adjusted demand, stock, lead time, safety stock, reorder point, and suggested order; the displayed planning table is also the input to `DataFrame.to_csv`.
6. **System Health & Model Insights** displays the same sensor/model/data status and describes the workflow.

Shared data is recomputed from session-state inputs in `utils/state.py`. It calls model inference with the four named features; snapshots the serial service; uses a recent live sensor reading only if the mode is Live Sensor and calibration is valid; otherwise it uses the simulation slider; applies the shared demand adjustment; computes reorder point/order/status. Detailed UI-to-source mapping is in [UI_ELEMENT_INVENTORY.md](UI_ELEMENT_INVENTORY.md); formulas are in [KPI_AND_FORMULA_REFERENCE.md](KPI_AND_FORMULA_REFERENCE.md).

## Sensor and firmware audit

`utils/sensor.py` parses the firmware format `Distance: <number> cm`, rejects malformed UTF-8/lines, `No echo detected`, non-finite values, and values outside 2–400 cm. It enumerates ports without opening them, auto-starts only for a single recognized USB candidate when enabled, and remains Simulated until a valid reading. The process-wide cached service owns a single reader thread, uses a 0.25 s serial read timeout, a 15 s first-valid-reading timeout, a 5 s stale limit, locks state, closes serial handles, and registers simulation cleanup at exit. Tests use a fake serial object.

The firmware source declares TRIG D1/GPIO5 and ECHO D2/GPIO4, 115200 baud, 30 ms `pulseIn` timeout, and a one-second reading interval. It calculates round-trip distance as `duration * 0.0343 / 2`, prints the parser-compatible line, and emits `No echo detected` on timeout. Its header and setup guide note the ECHO voltage concern and need for a level shifter/divider. Firmware compilation, actual wiring, voltage, and sensor readings are **not physically verified**.

The actual demo mount is horizontal through the box side. Active UI and setup wording now describe side-mounted distance toward the packages; the monotonic formula itself does not encode orientation. The physical target arrangement and one beam's reflecting surface mean the resulting percentage is an arrangement-specific occupancy index, not true volume or package count.

## Findings by priority

### Medium

1. **Sensor orientation wording — FIXED in targeted pass.** Initial evidence: `pages/2_Inventory_Digital_Twin.py:10`, `utils/inventory.py:25-29`, and `SENSOR_SETUP.md:3,38` described top-mounted use despite the supplied horizontal side mount. Current UI/setup text describes side-mounted distance toward the packages. Geometry still requires physical confirmation.
2. **Mixed-unit scenario chart — FIXED in targeted pass.** Initial evidence: `pages/4_Scenario_Simulator.py:51-55` used one axis for units/day and units. Current page renders separate daily-demand and inventory-quantity charts with distinct axis labels.
3. **Container-height behavior — EXPLAINED, calculation intentionally unchanged.** `app.py:37-40` describes its fallback role. `utils/state.py:64-68` passes explicit endpoints during normal operation, so height does not affect valid-calibration interpolation; `utils/simulation.py:12-20` uses container bounds only when calibration is invalid. This is the smallest safe choice without assuming container geometry can replace measured calibration.

### Low / informational

4. **MAE values were fixed literals — CLARIFIED.** `pages/3_AI_Demand_Forecast.py` displays notebook-reported reference values; the current evaluator separately reproduces them to two decimals. Page labels now state benchmark/reference and explain that no runtime evaluation occurs there. The fixed values can become stale if artifacts/data change.
5. **Calibration setup wording — UPDATED.** `SENSOR_SETUP.md` describes empty baseline and reference-target measurements for the side-mounted arrangement and says 0–100% are estimated endpoints, not verified physical fullness.
6. **“Previous week demand” input could mean a weekly total.** `app.py:47` is passed as `previous_week_demand`, but training code uses `demand.shift(7)`—the observation seven days earlier. Recommendation: clarify as “Demand 7 days ago.”
7. **CSS/utility residue.** `.status-pill` in `app.py:27`, `COLORS["navy"]`, and `empty_chart()` in `utils/ui.py` have no active callsite found. They are harmless but appear unused.

No critical or high-severity application defect was confirmed by this audit. This is not a claim of production readiness: sensor/browser verification and real demand evidence remain absent.

## Security, reliability, and maintainability

- The audit's filename/pattern search found no credential-bearing source file or `.env` configuration. No matching secret-like text was surfaced. This is a scoped source search, not a security scan of the Python environment or binary artifacts.
- No external API, database, authentication, file upload, or user-selected file path is present in the active app.
- Static app CSS is injected with `unsafe_allow_html=True`; the content is fixed project-authored CSS and does not interpolate user input.
- The model path is resolved from `utils/model.py` relative to the project, not the launch working directory.
- Serial parsing catches malformed messages; serial exceptions and timeouts switch inventory back to simulation. Thread code avoids Streamlit calls and has bounded reads/joins. Mock tests pass; physical driver/OS behavior remains unverified.
- The process-wide sensor service is shared, but planning controls are per browser session. Multiple concurrent users could influence the single hardware connection while seeing their own planning inputs; the project has no multi-user coordination or auth.
- No lockfile exists. Dependencies are ranges except `scikit-learn==1.6.1`; a fresh install can select newer pandas/NumPy/Streamlit/Plotly within those ranges.
- `refresh_shared_data()` is called from the sidebar fragment and again after navigation setup. This is redundant recomputation, though model loading is cached and the prediction itself is small.

## Verification boundary

Automated evidence is summarized in [TEST_AND_VERIFICATION_REPORT.md](TEST_AND_VERIFICATION_REPORT.md). AppTest is not a browser; no local browser automation was available. Hardware was not connected. Remaining unknowns and how to resolve them are itemized in [UNVERIFIED_ITEMS_AND_GAPS.md](UNVERIFIED_ITEMS_AND_GAPS.md). Demo readiness is conditional: software-only demo workflows render and the mocked suite passes, but the physical sensor cannot be represented as verified. See [DEMO_AND_VIVA_GUIDE.md](DEMO_AND_VIVA_GUIDE.md).
