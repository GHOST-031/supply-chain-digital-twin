# KPI and Formula Reference

This reference documents the formulas currently implemented, rather than substituting a different textbook definition. Source paths are relative to project root and line numbers refer to the audited source.

## Shared inventory and planning formulas

### KPI: Estimated Fill / Occupancy (%)

- **UI location:** Inventory Digital Twin page; sidebar metric; Executive Overview capacity delta.
- **Calculation source:** `utils/inventory.py:9-45`, called by `utils/state.py:19-46`.
- **Implementation:** endpoints are checked for numeric, finite values, full target `>= 0`, and empty baseline `> full target`. Measurement must be finite. It is clamped to the endpoint interval, then:

  `fill_percent = clamp(100 * (empty_distance - measured_distance) / (empty_distance - full_distance), 0, 100)`

- **Inputs/units:** distances in centimetres. `full_distance` is the calibrated full-distance target; `empty_distance` is the empty-box baseline; `measured_distance` is serial or simulated distance.
- **Source:** latest validated serial reading only in Live Sensor mode with valid calibration; otherwise the sidebar's simulated distance.
- **Example:** defaults empty 30.9 cm and target 2.6 cm. At 16.2 cm: `100*(30.9-16.2)/(30.9-2.6)=51.9434629%`, displayed as 51.9 or rounded to 52 depending on component.
- **Endpoints/bounds:** 30.9 -> 0%; 2.6 -> 100%; values farther than 30.9 clamp to 0%; values below 2.6 clamp to 100%; equal/reversed/non-finite/malformed endpoints are invalid; non-finite measurement raises `ValueError` at the utility layer. A finite negative distance passed directly to this utility clamps to the target-full endpoint, but the serial parser rejects values below 2 cm and the UI simulation slider itself starts at 0. `utils/simulation.py:8-25` falls back to `[0, container_height]` for invalid calibration. Shared state keeps inventory simulated if live data exists but calibration is invalid.
- **Verification:** 22-test suite includes endpoints, midpoint, measured intermediate values, clamp edges, invalid endpoints and NaN measurement. Independent results: 16.2 -> 51.9434628975%; 15.7 -> 53.7102473498%; 12.7 -> 64.3109540636%.
- **Limitations:** this is a calibrated distance index for the demonstrated side-mounted arrangement. A single reflecting beam is not a volume scan, weight measurement, or exact package counter. Target 2.6 cm is not experimentally established as physical full state. The mapping is only representative when the packages produce a consistent reflecting surface in the beam.

### KPI: Capacity-scaled inventory estimate (units)

- **UI location:** Inventory Digital Twin, Executive Overview, Scenario Simulator, Replenishment & Alerts.
- **Calculation source:** `utils/inventory.py:48-50`; shared `utils/state.py:39-46`; scenario `pages/4_Scenario_Simulator.py:27-30`.
- **Formula:** `max(0, capacity_units) * clamp(fill_percent, 0, 100) / 100`.
- **Inputs/units:** configured capacity units; occupancy percentage points. Output is capacity-scaled configured units.
- **Example:** default capacity 100 and simulated distance 17 cm -> 49.1166078% -> 49.1166078 configured units; Overview rounds this to `49 units`, Inventory and Alerts show `49.1 units`.
- **Edge handling:** negative capacity is floored at zero; fill is clamped. The sidebar constrains capacity to 10–1000. No sensor-derived package count calibration exists.
- **Verification:** existing regression test checks 100 capacity at 50% -> 50; AppTest shows default inventory `49.1 units`.
- **Limitations:** units are not an observed count; capacity is a user-configured scale factor.

### KPI: Base model prediction (units/day)

- **UI location:** Executive Overview and AI Demand Forecast.
- **Calculation source:** `utils/model.py:10-60`, features assembled in `utils/state.py:49-60`.
- **Model:** stored V2 `LinearRegression`, loaded from project-root `demand_model_v2.joblib`; features are passed in stored order: `previous_day_demand`, `previous_week_demand`, `rolling_7_day_avg`, `day_of_week`.
- **Mathematical form:** `prediction = intercept + Σ(coef_i * feature_i)`, then the app returns `max(0, prediction)`. Stored coefficients (rounded for explanation): intercept 6.7594138; coefficients `[0.4927750, -0.0961599, 0.4042409, -0.7380570]` in the order above.
- **Input definitions:** previous day is manually entered demand; “Previous week demand” is actually the one-day observation lagged seven days in training; rolling average is supplied manually; weekday is Monday=0 through Sunday=6.
- **Units/source:** demand inputs and result are synthetic/demo or manually configured units per day; no observed warehouse series feeds these controls.
- **Example:** inputs 22, 20, 21, 4 produce `21.2140966405 units/day` (UI `21.21`).
- **Validation:** input keys must exist; all are numeric and finite; first three are nonnegative; weekday must be an integer member of 0..6; non-finite prediction errors; negative result clipped to zero. Errors are returned, surfaced in the UI, and downstream recommendations are stopped.
- **Verification:** model status loaded V2 without warning under sklearn 1.6.1; existing model test asserts feature order and nonnegative prediction. The evaluator independently loaded V2.
- **Limitations:** model performance evidence is synthetic only. There is no live retraining, confidence interval, or ultrasonic sensor input to this model.

### KPI: Adjusted / planning demand (units/day)

- **UI location:** overview caption, forecast caption, shared recommendation calculations, scenario baseline.
- **Calculation source:** `utils/state.py:72-75`.
- **Formula:** `max(0, base_prediction * (1 + demand_change_percent/100))`.
- **Example:** 21.2140966 base prediction and +20% shared change -> 25.4569160 units/day (`25.5` shown).
- **Assumptions:** demand change is a hypothetical multiplier from -50% to +100%; it is not a model prediction.
- **Verification:** AppTest showed 25.5 baseline demand; changing the scenario adjustment changed demand to 31.8 units/day.
- **Limitations:** the app uses this adjusted demand for planning but preserves base prediction separately.

### KPI: Reorder point (units)

- **UI location:** Overview, scenario comparison and KPI, replenishment page, inventory history reference line.
- **Calculation source:** `utils/inventory.py:52-54`, called from `utils/state.py:76` and `pages/4_Scenario_Simulator.py:29`.
- **Formula:** `max(0, daily_demand) * max(0, lead_time_days) + max(0, safety_stock_units)`.
- **Inputs/units:** adjusted demand in units/day; lead time in days; safety stock in configured units. Output is configured inventory units.
- **Example:** default adjusted demand 25.4569160 × 3 days + 10 units = 86.3707479 units (`86.4`).
- **Edge handling:** negative arguments are floored to zero by function; UI controls constrain lead to 1–30 and safety stock to 0–10000. A prediction failure produces no reorder point.
- **Verification:** regression test `reorder_point(10,5,7)==57`; AppTest rendered 86.4; scenario lead-time changes altered the expected KPI.
- **Limitations:** this deterministic threshold assumes a constant daily demand across supplier lead time; it is not a probabilistic service-level calculation.

### KPI: Suggested replenishment/order (units)

- **UI location:** Overview, Scenario Simulator, Replenishment & Alerts, downloadable planning row.
- **Calculation source:** `utils/inventory.py:56-58`, shared call at `utils/state.py:99`.
- **Formula:** `max(0, ceil(max(0, reorder_point - max(0, stock))))`.
- **Example:** reorder 86.3707479 minus stock 49.1166078 = 37.2541401; ceiling -> 38 units.
- **Units/source:** configured units; stock comes from capacity-scaled occupancy; reorder point comes from planning demand.
- **Verification:** tests check 50 vs 57 -> 7, and stock above reorder -> 0. Overview/AppTest and Replenishment page both showed 38 units.
- **Limitations:** amount is a recommendation to bring estimated stock to at least threshold, rounded upward. It does not place an order or contact a supplier. It compounds uncertainty in occupancy and synthetic demand.

### KPI: Estimated days of stock

- **UI location:** Overview and Scenario Simulator.
- **Calculation source:** `utils/inventory.py:60-63`; overview `pages/1_Executive_Overview.py:20-21`; scenario `pages/4_Scenario_Simulator.py:31-33`.
- **Formula:** `max(0, stock) / daily_demand` only when demand `> 0`, otherwise `None`.
- **Units:** configured units divided by configured units/day -> days.
- **Example:** 49.1166078 / 25.4569160 = 1.9294013 days (`1.9`).
- **Invalid behavior:** zero or negative demand yields unavailable (`—` on Overview); no divide-by-zero.
- **Verification:** default AppTest displayed 1.9; source inspected. No standalone unit test for `days_of_stock` was found.
- **Limitations:** assumes a constant adjusted demand rate and a capacity-scaled stock estimate.

### KPI: Inventory health/status

- **UI location:** Overview alert and Inventory Digital Twin status message.
- **Calculation source:** `utils/inventory.py:65-72`; surfaced by `utils/state.py:103`.
- **Rules in order:** Critical if fill <=10% or stock <=0; otherwise Reorder required if stock <= reorder point; otherwise Low if fill <=30%; otherwise Healthy.
- **Inputs:** occupancy percentage, stock units, reorder point units.
- **Example:** default fill 49.12%, stock 49.12, reorder 86.37 -> `Reorder required` because stock <= reorder point.
- **Verification:** source inspected; pages render. No exhaustive threshold unit-test matrix exists.
- **Limitations:** threshold classification, not a health score or forecast probability. Reorder check precedes Low, so `Low` applies only when fill <=30% and stock exceeds reorder point; critical takes precedence.

### KPI: Replenishment urgency

- **UI location:** Replenishment & Alerts warning/success text and CSV table.
- **Calculation source:** `pages/5_Replenishment_Alerts.py:21-26`.
- **Rules:** if stock <= reorder point, urgency is `Urgent` when stock <= safety stock, otherwise `Plan now`; if stock > reorder point, urgency is `Monitor`.
- **Example:** default stock 49.1 > safety 10 and <= reorder 86.4 -> `Plan now`.
- **Verification:** default AppTest showed warning branch and the table's `Plan now` state.
- **Limitations:** `Urgent` is a fixed threshold label, not probability of stockout, supplier feasibility, or a risk score.

### KPI: Scenario reorder threshold (Reached / Not reached)

- **UI location:** Scenario Simulator fifth metric.
- **Calculation source:** `pages/4_Scenario_Simulator.py:48-49`.
- **Formula:** reached exactly when scenario stock <= scenario reorder point.
- **Example:** default scenario stock about 49 versus reorder 86.4 -> Reached.
- **Verification:** AppTest default state showed Reached; changing each of five form inputs changed its expected outputs.
- **Limitations:** this is a threshold flag, not stockout risk probability.

## Sensor/serial calculations

### Serial distance parsing and validation

- **Source:** `utils/sensor.py:70-94`.
- **Format:** case-insensitive full-line match `Distance: numeric-value cm` (supports sign/decimal syntax), or exact trimmed `No echo detected` special case.
- **Range:** 2.0–400.0 cm inclusive. `No echo` is not a distance and never activates Live Sensor. Invalid encoding, empty/malformed strings, NaN/Inf, and out-of-range values are rejected.
- **Units:** centimetres from firmware output.
- **Verification:** mocked parser tests cover valid, no echo, malformed UTF-8/text, and range/nonfinite values.

### Firmware distance calculation

- **Source:** `firmware/esp8266_hcsr04.ino:29-46`.
- **Formula:** `distance_cm = echo_duration_microseconds * 0.0343 cm/µs / 2` (divide by two for outbound and return travel).
- **Configuration:** TRIG D1/GPIO5, ECHO D2/GPIO4; Serial 115200; `pulseIn` timeout 30000 µs; interval 1000 ms.
- **Verification:** source inspected; parser-compatible literal output confirmed by comparison. Not compiled/uploaded or physically measured.

## Synthetic histories and evaluation formulas

- **Synthetic demand target:** `training/generate_dataset.py:19-38`, mirrored in the notebook. With day index `d=0..364`: `trend = 20 + 0.02*d`; `weekly = 3*sin(2*pi*d/7)`; `seasonal = 4*sin(2*pi*d/30)`; `noise ~ Normal(0,2)` using NumPy seed 42; `demand = int(max(1, round(trend + weekly + seasonal + noise)))`. Features are prior-day `demand.shift(1)`, prior-week `demand.shift(7)`, and prior-seven-row mean from `demand.shift(1).rolling(7).mean()`; first seven rows are dropped; weekday is `(day-1)%7`. These are generated values and no real seasonality or stochastic process has been validated.

- **Demand demo history:** `utils/simulation.py:28-35`. A seeded Normal(0,2) perturbation is added to weekday pattern `[19.5,20.2,21.0,22.4,24.1,17.8,16.2]` and a linear trend from -1.2 to +1.2; negative values are clipped to zero. Not observed demand and separate from training CSV.
- **Inventory demo history:** `utils/simulation.py:38-49`. Creates a linear trend from `min(capacity, max(0, current_stock + days*1.2))` to current stock, adds seeded interior Gaussian noise with std `max(0.1, capacity*0.018)`, clips to [0, capacity], and pins final point to current estimate. Not sensor history.
- **Mean absolute error:** evaluator uses sklearn `mean_absolute_error(y_test,prediction)`, equivalent to `mean(abs(actual-predicted))`, on 72 chronological held-out synthetic rows. Previous-day baseline uses test `previous_day_demand` as prediction. Results are recorded in the audit report.
- **Notebook V1 relative improvement:** notebook output cell computes `(baseline_mae - model_mae) / baseline_mae * 100` when baseline is nonzero, otherwise zero. The stored notebook output reports 3.55% for V1 vs baseline using unrounded MAEs. No percentage is displayed by the active dashboard.
- **Weekday pattern:** `pages/3_AI_Demand_Forecast.py:25-30` groups the 30-row visual synthetic series by date-derived weekday and averages `demand_units`. It is a chart aggregation, not evaluation data.

## Cross-page consistency and caveats

Base model prediction is separate from adjusted planning demand. `utils/state.py` computes both once and supplies every page. Replenishment and reorder calculations consume the adjusted value; the forecast page displays both. Scenario baseline uses shared values while hypothetical form values are independent after interaction. CSV is built from the same one-row DataFrame shown on screen, but actual downloaded bytes were not validated in a browser; see test report.

The default numerical chain is:

| Step | Value |
|---|---:|
| V2 prediction from 22, 20, 21, weekday 4 | 21.2141 units/day |
| Shared demand adjustment | +20% |
| Planning demand | 25.4569 units/day |
| Simulated distance | 17.0 cm |
| Fill / occupancy index | 49.1166% |
| Configured capacity and estimated stock | 100 units -> 49.1166 scaled units |
| Lead time / safety stock | 3 days / 10 units |
| Reorder point | 86.3707 units |
| Suggested order | 38 units |
| Days of stock | 1.9294 days |

This chain is an example using current defaults, not a live sensor observation or a validated warehouse plan.
