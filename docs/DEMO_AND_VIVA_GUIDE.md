# Demonstration and Technical Viva Guide

The checks below describe the software as inspected. The sensor and physical geometry are not hardware-verified. Say “calibrated occupancy estimate” rather than “measured volume” or “exact number of packages.” The 2.6 cm endpoint is a target; do not call the box physically full unless that state is independently confirmed.

## Demonstration checklist

| Step | Action | Expected UI/calculation | What to say if asked | What could go wrong | Safe recovery |
|---|---|---|---|---|---|
| 1. Environment | From project root activate `.venv`; run `streamlit run app.py` | Local Streamlit app opens on Executive Overview; six navigation entries appear | “The UI uses Streamlit; calculations are shared through session state.” | Wrong environment or missing dependencies | Activate the project environment and check package installation; do not upgrade sklearn/model files during demo |
| 2. Simulation baseline | Start with no device connected | Sidebar says Simulated; default simulated distance 17 cm; fill about 49.1%, stock 49.1/100 units | “A detected port is not live mode; only a recent valid line enables Live Sensor.” | Existing session has user-modified values | Review sidebar values; use simulation controls explicitly |
| 3. Explain calibration | Show target 2.6 cm and empty baseline 30.9 cm | Empty endpoint 0%; target endpoint 100%; the current simulated distance is interpolated | “2.6 cm is a calibrated distance target, not a claim that this arrangement is physically full.” | Question about what container height changes | Explain that explicit calibration endpoints govern normal mapping; container height is used for invalid-calibration simulation fallback |
| 4. Show inventory | Open Inventory Digital Twin | Capacity, container height, distance, fill bar, capacity-scaled units, status, demo history, and ROP line appear | “The sensor observes the nearest reflecting surface along one beam. The percentage is arrangement-specific and does not measure volume or count packages.” | Someone interprets units as exact packages | Point to the on-page capacity-scaling caveat |
| 5. Show forecast | Open AI Demand Forecast | V2 shows 21.21 units/day at current default features; 30-day synthetic visual chart and weekday averages appear | “This is one model prediction from manually controlled inputs; charts are separate synthetic demo data.” | Asked whether charts are observed warehouse demand | They are generated for illustration; no observed history is present |
| 6. Explain evaluation | Show MAE comparison and System Health | 2.09 V2 vs 2.31 previous-day baseline; synthetic limitation is stated | “These are reproduced on the generated 358-row synthetic dataset and 72-row chronological holdout; they are not real warehouse accuracy.” | Asked to reproduce exact metric | `./.venv/bin/python -B training/evaluate_models.py` |
| 7. Scenario case | Set one or more hypothetical form controls; click Apply scenario | Demand, ROP, order, days, threshold, table and unit-separated charts recompute | “Scenario inputs are hypothetical and separate from shared baseline controls.” | Form values look different from shared inputs after prior use | Explain that scenario widget keys retain their own submitted what-if values; baseline still follows current shared controls |
| 8. Replenishment | Open Replenishment & Alerts | Current stock, ROP, order, lead, safety, urgency, table and CSV button appear | “Suggested order is a planning calculation only; it does not contact a supplier.” | Stock appears decimal but suggested order integer | Explain order rounds the deficit upward using ceiling |
| 9. CSV | Click Download recommendation CSV | Browser should download `replenishment_recommendation.csv` generated from the visible one-row table | “The file contains the displayed planning row; it does not record a placed order.” | Download blocked or browser prompts | Use the download control again / browser download shelf; do not claim transfer was verified by AppTest |
| 10. System health | Open System Health & Model Insights | Shows current mode, connection state, model loaded/features, warnings, input/calibration and provenance status | “The model and sensor integration boundaries are visible; current session is still simulation absent live data.” | Model missing or warning appears | Stop relying on the forecast; show the visible error; do not replace artifact during demo |
| 11. Optional hardware | Close Arduino Serial Monitor; attach known device, refresh ports, select correct port or allow unique-candidate auto-connect | Connecting remains simulated until parser accepts a recent `Distance: … cm` line; then Live Sensor appears | “The software has a mock-tested serial path, but this specific physical setup is only validated during the demonstration.” | Port busy, no echo, wrong port/baud, or voltage/wiring issue | Disconnect/switch to simulation, close other serial clients, confirm cable/port/115200 and safe ECHO level shifting; do not change wiring live without supervision |
| 12. Fallback | Stop firmware or disconnect via app; optionally wait past stale limit | State becomes Disconnected/Error and inventory source returns to Simulation | “Stale or failed serial data is not reused as live inventory.” | Reader still stopping | Wait briefly for bounded read timeout/cleanup; choose Switch to simulation |
| 13. Clean shutdown | Stop Streamlit with Ctrl+C; close Serial Monitor/IDE serial session | Cached service shutdown attempts to return to simulation and close port | “The serial service registers process-exit cleanup.” | Another app owns port | Close the competing serial program first |

### Startup commands

For an existing project environment:

From the project root, activate the existing environment and start the app:

```bash
source .venv/bin/activate
streamlit run app.py
```

To repeat software checks without installing packages:

```bash
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B training/evaluate_models.py
```

## Architecture and subsystem explanation

- **Frontend:** `app.py` defines the wide Streamlit shell, shared sidebar controls, sensor status/control fragment, and native `st.navigation` pages.
- **Shared calculations:** `utils/state.py` composes model prediction, inventory source, fill/stock, adjusted demand, reorder point, order, days/status into `st.session_state.app_data`.
- **Inventory:** `utils/inventory.py` contains formula functions used by state and scenario code; pages format values but do not implement a separate shared reorder formula.
- **Demand model:** V2 is a serialized `sklearn.linear_model.LinearRegression`, with features previous-day demand, demand seven days earlier, prior-seven-day average, and day-of-week integer. `utils/model.py` loads it with `st.cache_resource` and builds a named-column DataFrame in stored order.
- **Sensor:** Python enumerates ports through pyserial and owns a single cached `SensorService` reader. Firmware sends line-oriented distance strings at 115200 baud. Simulation is the fallback.
- **Demo histories:** `utils/simulation.py` uses seeded synthetic functions; these are not retained sensor observations. The inventory history is generated to end at current estimate.
- **Training/evaluation:** the notebook and `training` scripts are separate from app startup. Evaluator loads existing V1/V2 models and evaluates held-out synthetic rows; generator can rewrite the CSV if run with default output, so it was not run during this audit.
- **Testing:** unittest uses a mocked serial object. AppTest validates Streamlit script rendering, not browser visual behavior or hardware.

## Technical viva questions and evidence-based answers

1. **What is the app entry point?** `app.py`; launch with `streamlit run app.py`.
2. **How many pages are registered?** Six `st.Page` objects in `app.py:148-155`, in navigation order listed in the project audit.
3. **How do pages get common calculations?** `refresh_shared_data()` stores a dictionary at `st.session_state.app_data`; `utils.ui.shared_data()` reads it.
4. **Which model is used in production?** `demand_model_v2.joblib`, loaded from a project-relative path in `utils/model.py`; V1 is retained for comparison.
5. **What kind of estimator is it?** `LinearRegression` with four features for V2; V1 has three.
6. **What is the V2 feature order?** `previous_day_demand`, `previous_week_demand`, `rolling_7_day_avg`, `day_of_week`.
7. **What does “previous week demand” mean in training?** `demand.shift(7)`, i.e. a lagged daily observation seven days earlier, not a weekly sum.
8. **How is weekday encoded?** Monday 0 through Sunday 6; generator/notebook uses `(day-1)%7`, and inference maps the selected weekday via its list index.
9. **How does the inference layer keep feature names/order?** It builds a one-row pandas DataFrame with columns in `MODEL_FEATURES` order before `predict`.
10. **How are invalid demand inputs handled?** Missing/non-numeric/non-finite values, negative demand inputs, invalid weekday, or non-finite prediction return an error; negative output is clipped to zero.
11. **What is base versus planning demand?** Base is the raw V2 prediction. Planning demand multiplies base by `(1 + shared percent/100)` and is used for ROP and days of stock.
12. **What does the ultrasound sensor measure?** Time delay for an ultrasonic echo, converted to distance; it does not measure packages, mass, or volume.
13. **What pins does the firmware define?** TRIG D1/GPIO5, ECHO D2/GPIO4; the code comments require safe 5 V to 3.3 V ECHO interfacing.
14. **What is the distance equation?** Echo duration in microseconds × 0.0343 cm/µs divided by two for round trip.
15. **What serial protocol does Python expect?** A full line like `Distance: 24.5 cm`; `No echo detected` is treated as no measurement.
16. **What baud rate is used by default?** 115200 in firmware and Python sensor service/sidebar.
17. **When does the app call data Live Sensor?** Only after a parser-valid distance is received and remains within the configured freshness limit; port detection by itself is insufficient.
18. **What happens with stale data?** Service transitions to Disconnected/Error, closes the serial handle and inventory calculation uses simulation.
19. **How long is a reading considered fresh?** The service default stale threshold is 5 seconds; first valid reading timeout is 15 seconds.
20. **Why have a simulation fallback?** The app remains usable without hardware and does not misrepresent simulated measurements as physical data.
21. **What calibration endpoints are configured?** Full-distance target 2.6 cm, empty-box baseline 30.9 cm.
22. **What is the fill formula?** Clamp `100*(empty-measured)/(empty-full)` to [0,100].
23. **What do the known distances map to?** 30.9→0%, 2.6→100%, 16.2→51.94%, 15.7→53.71%, 12.7→64.31%.
24. **Does 100% prove the cardboard box is physically full?** No. It means only that measured distance reached the configured calibrated target; physical full-state validation is not evidenced.
25. **How is stock quantity estimated?** `capacity * fill_percent / 100`, with nonnegative capacity and bounded percentage.
26. **Is that an exact package count?** No. It is capacity-scaled occupancy estimate; package count, volume and mass are not directly measured.
27. **What is the reorder-point equation?** `scenario_demand * lead_time_days + safety_stock` after each input is floored at zero.
28. **How is suggested order rounded?** Ceiling of positive reorder-point deficit versus nonnegative estimated stock; zero if no deficit.
29. **What is days of stock?** Nonnegative stock divided by positive adjusted demand; unavailable when demand is zero/nonpositive.
30. **How is inventory status classified?** Critical at fill <=10% or stock <=0; then Reorder required if stock <= ROP; then Low at fill <=30%; otherwise Healthy.
31. **What does `Urgent` mean on Alerts?** The threshold label when stock is at/below safety stock while also below/at reorder point; it is not a statistical risk estimate.
32. **How is scenario analysis different from baseline?** It takes independent form controls for scenario demand percent, lead, capacity, inventory percent and safety stock; it recomputes stock, ROP, order and days without changing shared baseline controls.
33. **What synthetic data was used for training?** 365 seeded generated days with trend, weekly/monthly sine components and Gaussian noise; lag/rolling rows reduce it to 358 usable records.
34. **What split is used for reported MAE?** First 286 rows train and last 72 test, chronological 80/20 row split.
35. **What is the baseline forecast?** Previous-day demand feature used directly as held-out prediction.
36. **What are the current reproduced MAEs?** V1 2.2236285, V2 2.0868999, baseline 2.3055556 units/day, rounding to 2.22/2.09/2.31.
37. **Are these metrics real warehouse accuracy?** No, they are evaluated on synthetic generated data only.
38. **Does the app retrain the model?** No. App loads the V2 artifact; training/evaluation scripts are separate and evaluator does not fit/save.
39. **Does sensor data feed demand forecast?** No. Sensor reading is used for inventory estimate; model inputs come from shared demand controls.
40. **What does the CSV download do?** Serializes the one-row planning DataFrame; it is a recommendation report, not proof an order was placed.
41. **What is covered by serial tests?** Parser formats, no-echo/malformed/out-of-range, mocked port failures, timeout, live transition, stale/disconnect fallback and no duplicate active open.
42. **Have the physical firmware or sensor been verified?** No; source and parser compatibility were inspected, but there was no upload, wiring, voltage, real reading, or physical calibration test.
43. **Why can the chart not prove historic stock levels?** Inventory history is seeded synthetic demonstration data whose final point is set to current estimate; no sensor history is persisted.
44. **What is one remaining presentation limitation?** Scenario demand and inventory are now shown in separate charts because units/day and inventory units are not directly comparable. Some older audit text records the original issue; the current UI and setup guide describe side mounting.

## Limitations to state plainly

No observed warehouse demand, package count, scale weight, stored sensor history, physically validated full-state calibration, real browser test, firmware build, or hardware session was available. UI wording should not be used to imply any of these have been verified.
