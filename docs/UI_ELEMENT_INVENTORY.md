# UI Element and Interaction Inventory

Audit of UI construction in `app.py` and all six page scripts. Values and status text in this file are the current source literals; runtime numbers depend on session controls and sensor state. Line references are project-relative. AppTest rendered each page, but there was no full browser interaction or hardware session.

## Global shell and sidebar (`app.py`)

| Exact visible text / element | Type and default/range | Source | Behavior / state effect | Verification |
|---|---|---|---|---|
| Browser title `Supply Chain Digital Twin` | Streamlit page config, wide layout | `app.py:19` | Sets title/layout only | AppTest ran |
| Static CSS | Metric cards pale blue, rounded; headings slight negative letter spacing; container top/bottom padding; `.status-pill` definition | `app.py:21-29` | Presentation only; no inputs; fixed source CSS through `unsafe_allow_html` | Source inspected; browser appearance not verified; status-pill class has no use found |
| `Supply Chain Digital Twin` | Sidebar title | `app.py:31` | Static | AppTest ran |
| `Inventory monitoring · demand planning` | Sidebar caption | `app.py:32` | Static | AppTest ran |
| `---` | Sidebar divider | `app.py:33,50,102` | Static spacing | AppTest ran |
| `Shared planning inputs` | Sidebar section header | `app.py:34` | Static | AppTest ran |
| `These controls update the figures across all pages.` | Caption | `app.py:35` | Explains shared controls | Source inspected; AppTest pages run |
| `Storage capacity (units)` | Number input; default 100, min 10, max 1000; key `capacity` | `app.py:36` | Scales occupancy to estimated units; affects shared stock/order/status and graphs | AppTest default inspected |
| `Container height (cm)` | Slider; default 50, min 10, max 200; key `container_height`; help says it is used for container-bound simulation fallback when calibration endpoints are invalid | `app.py:37-40` | With valid explicit endpoints, distances determine occupancy and changing height does not alter the estimate | Source and calibration behavior tested |
| `Calibrated full-distance target (cm)` | Number input; default 2.6, range 0–200; key `valid_min_distance` | `app.py:38` | Calibration endpoint; changes fill and derived stock across pages | AppTest fresh-session default verified |
| `Empty-box baseline distance (cm)` | Number input; default 30.9, range 0.1–200; key `valid_max_distance` | `app.py:39` | Calibration endpoint; changes fill and derived stock | AppTest fresh-session default verified |
| Calibration target caveat | Caption: full-distance value is target, not proof box is full unless experimentally validated | `app.py:40` | Static qualification | Source inspected; page rendered |
| `Simulated sensor distance (cm)` | Slider; default 17, min 0, max 200; key `distance_cm` | `app.py:41` | Supplies fallback measurement when no valid live/calibration path is active | Source inspected; mock tests cover fallback, not slider interaction |
| `Demand change (%)` | Slider; default +20, range -50 to +100; key `demand_change` | `app.py:42` | Multiplies base prediction for planning demand | AppTest displayed adjusted demand |
| `Supplier lead time (days)` | Slider; default 3, range 1–30; key `lead_time` | `app.py:43` | Reorder-point input | AppTest displayed resulting ROP |
| `Safety stock (units)` | Number input; default 10, range 0–10000; key `safety_stock` | `app.py:44` | Added to reorder point | AppTest displayed resulting ROP |
| `Demand model inputs` | Expander | `app.py:45` | Opens/closes inputs; no calculation until rerun | Source inspected; not browser-tested |
| `Previous day demand` | Number input; default 22, range 0–10000; key `previous_day` | `app.py:46` | V2 feature input | Source inspected; inference test uses 22 |
| `Previous week demand` | Number input; default 20, range 0–10000; key `previous_week` | `app.py:47` | V2 feature `previous_week_demand` (training means demand seven days earlier) | Source inspected; label ambiguity noted |
| `7-day rolling average` | Number input; default 21, range 0–10000; key `rolling_avg` | `app.py:48` | V2 rolling feature input | Source inspected; inference test uses 21 |
| `Day of week` | Selectbox Monday–Sunday, default current local weekday; key `weekday` | `app.py:49` | Mapped to model integer Monday=0 … Sunday=6 | Source inspected; AppTest render |
| `Ultrasonic sensor` | Sidebar section header | `app.py:51` | Static | AppTest ran |
| Sensor controls refresh | Fragment with `run_every=1.0` | `app.py:54-55` | Re-runs sensor status/polling at one-second interval; one process-wide service | AppTest render; no browser timing test |
| `Serial baud rate` | Number input; default 115200, min 1200, max 1,000,000, step 1200; key `sensor_baud_rate` | `app.py:57-60` | Used when starting serial reader | AppTest default indirect; mocked service verifies 115200 default |
| `Auto-connect when one USB serial device is found` | Checkbox, default checked; key `sensor_auto_connect` | `app.py:61-64` | When exactly one recognized candidate exists and service is idle/error, attempts connection; USB discovery alone remains non-live | Mock service tests unique vs ambiguous behavior |
| `Refresh serial ports` | Button; key `refresh_sensor_ports` | `app.py:65-67` | Clears auto-attempt suppression; current rerun re-enumerates ports | Source inspected; not physically tested |
| Multiple-device warning | `Multiple USB serial devices found. Choose a port and connect manually.` | `app.py:81-82` | Shown only with auto mode and >1 candidate | Source inspected; mock tests ambiguity; no visual test |
| `Serial port` | Selectbox of discovered port labels, or disabled `No serial ports detected` | `app.py:83-89` | Selects manual connection candidate; does not connect by itself | AppTest on host saw a port list entry; no port opened by test |
| `Connect` | Button; disabled if no selected port | `app.py:91-95` | Starts background reader; state becomes Connecting; stays simulated until validated reading | Mock serial tests cover lifecycle; no real port |
| `Disconnect` | Button; disabled unless Connecting or Live Sensor | `app.py:96-97` | Stops reader and leaves state Disconnected/Error while inventory mode is simulation | Mock tests cover disconnect fallback |
| `Switch to simulation` | Button; disabled if already Simulated | `app.py:98-99` | Disconnects reader, clears live reading, and selects Simulated | Mock tests cover manual fallback |
| `Shared sensor status` | Bold section label | `app.py:103` | Static | AppTest ran |
| `Mode`, `Connection`, `Port`, `Baud` | Dynamic lines | `app.py:104-106` | Reflect shared service snapshot; mode Simulated unless a recent valid reading exists | Mock tests verify state transitions |
| `Latest valid distance` | Dynamic value or em dash | `app.py:107-114` | Shows last accepted live distance only; otherwise blank marker | Mock service reading tested, UI render only |
| `Received (UTC): … · age …` | Dynamic timestamp/age caption | `app.py:108-112` | UTC ISO timestamp and monotonic age; labels stale if unavailable | Mock timestamps; no browser elapsed-time test |
| Calibration invalid warning / calibration caption | Dynamic error or `Calibration: full … cm · empty … cm` | `app.py:115-120` | Shared validator checks endpoints; changes reflect rerun | Invalid calibration unit test and default AppTest |
| Simulation/Connecting/Live/Error status messages | info, info, success, or warning | `app.py:121-128` | Selected by explicit connection state; simulation says port alone does not enable live | Sensor service tests exercise transitions |
| Connection feedback / serial error | Error message plus install/reconnect/close-monitor guidance | `app.py:129-143` | Shown on failed connect or missing pyserial/ports | Source inspected; mocked port-unavailable tested |
| `{inventory_source} calibrated fill` | Sidebar metric, one decimal percent | `app.py:132-135` | Current shared estimate; refreshes with state | AppTest rendered; calculation tests |
| Six nav labels | `Executive Overview`; `Inventory Digital Twin`; `AI Demand Forecast`; `Scenario Simulator`; `Replenishment & Alerts`; `System Health & Model Insights` | `app.py:148-156` | Native Streamlit navigation; first page default | AppTest `switch_page` rendered all six |

## Page 1 — Executive Overview

Source: `pages/1_Executive_Overview.py`.

| Exact visible text / element | Type, dynamic source | Interaction/calculation | Verification |
|---|---|---|---|
| `Executive Overview` | Title via `page_header`, line 11 | Static | AppTest rendered |
| `A concise view of estimated inventory, demand pressure, and the next replenishment decision.` | Caption, line 11 | Static | AppTest rendered |
| Missing shared inputs error | `Shared application inputs are not available. Return to the main app and reload.`; lines 12–14 | Stops page if `app_data` empty | Branch source inspected, branch not forced |
| `Estimated stock` | Metric, `stock` rounded 0 decimals and fill rounded 0 in delta; line 16 | Shared occupancy estimate/capacity | AppTest rendered 49 units; underlying 49.1 |
| `Base model prediction` | Metric, `predicted_demand` one decimal units/day or Unavailable; line 17 | Does not include planning adjustment | AppTest rendered 21.2 |
| `Reorder point` | Metric, shared ROP one decimal or Unavailable; line 18 | Reorder formula | AppTest rendered 86.4 |
| `Suggested replenishment` | Metric, integer units or Unavailable; line 19 | Shared suggested order | AppTest rendered 38 |
| `Days of stock` | Metric one decimal days or em dash; help says unavailable at zero/invalid demand; lines 20–21 | Uses adjusted planning demand | AppTest rendered 1.9 days |
| `Planning demand: … after the …% shared demand adjustment…` | Conditional caption; lines 22–27 | Shows adjusted value and its role | AppTest rendered |
| Inventory health `Critical` / `Reorder required` / `Low` / `Healthy` messages | Conditional error/warning/success; lines 29–36 | Threshold/status branches from shared data | Default reorder branch rendered; thresholds source inspected |
| Sensor mode/info | `Sensor mode: **…**. Inventory source: **…**.`; line 37 | Mirrors current shared service + chosen inventory source | AppTest rendered simulated mode |
| Demand prediction unavailable | Conditional error with error detail; lines 38–39 | Appears on prediction failure | Branch inspected, not forced in AppTest |
| `Recent demand and estimated inventory` | Section header; line 41 | Static | AppTest rendered |
| Demand trend chart | 30-day `Synthetic demand` trace; dashed `Current model prediction`; y-axis `Units / day`; lines 43–49 | Default Plotly hover shows date/value and trace name; no custom hover template or controls | AppTest rendered; chart trace source inspected |
| Stock trend chart | 14-day `Simulated stock`; filled line; dashed `Reorder point`; y-axis `Estimated units`; lines 50–53 | Default Plotly hover shows date/value and trace name; demo series ends at current estimated stock | AppTest rendered |
| Synthetic-history disclosure | `Both history series are reproducible synthetic demonstrations…`; line 54 | Clarifies provenance | AppTest rendered |

## Page 2 — Inventory Digital Twin

Source: `pages/2_Inventory_Digital_Twin.py`.

| Exact visible text / element | Type, dynamic source | Interaction/calculation | Verification |
|---|---|---|---|
| `Inventory Digital Twin` | Title, line 10 | Static | AppTest rendered |
| `Convert a side-mounted ultrasonic distance reading toward the packages into a calibrated occupancy estimate.` | Caption, line 10 | Static | AppTest rendered |
| `Current inventory source: …` disclosure | Caption; line 11 | Shows Simulation or Live Sensor and live-reading/calibration gate | AppTest rendered simulation |
| `Storage capacity`, `Container height`, `Sensor to stock surface` | Three metrics; lines 12–15 | Shared controls/current distance | AppTest rendered defaults 100, 50, 17 |
| `Estimated Fill / Occupancy (%)` | Bar-chart section title; lines 21–25 | Bar category `Estimated Fill / Occupancy`; y-axis title `Fill`, range 0–100%, tick suffix `%`, in-bar integer percent; progress widget repeats value | AppTest rendered; test formulas |
| `Estimated inventory` | Section title; line 27 | Static | AppTest rendered |
| `Capacity-scaled inventory estimate` | Metric; one-decimal units; delta occupancy estimate; line 28 | Percent × capacity | AppTest rendered 49.1 units |
| `Reading status: …` | Dynamic text; line 29 | Live/simulated status description | AppTest rendered |
| `Calibration range: full-distance target …; empty-box baseline …` | Dynamic text; line 30 | Values in cm; clamped output | AppTest default values |
| Target-endpoint caveat | Caption; line 31 | Says target does not mean physical full unless validated | AppTest rendered |
| Smaller-gap / clamping note | Text; line 32 | Explains direction of estimate | AppTest rendered |
| Arrangement / non-volume caveat | Caption; line 33 | Disclaims exact count/volume and explains scaling/replenishment use | AppTest rendered |
| Invalid-calibration warning | Conditional warning; line 35 | Says fallback uses container bounds | Invalid-calibration test, branch not force-rendered |
| Inventory level status | Critical/error, reorder/warning, low/warning, else healthy/success; lines 36–39 | Uses shared status thresholds | Default branch rendered; other branches inspected |
| `Demonstration inventory history` | Section title; line 41 | Static | AppTest rendered |
| Inventory chart | 14-day `Simulated stock`, markers/area; dashed red annotation `Reorder point`; y-axis `Estimated units`; lines 42–50 | Default Plotly hover shows date, stock value and trace; synthetic history ends at current estimate; shared ROP reference | AppTest rendered |
| History disclosure | Caption says not recorded sensor history even if current endpoint is live; line 51 | Static qualification | AppTest rendered |

## Page 3 — AI Demand Forecast

Source: `pages/3_AI_Demand_Forecast.py`.

| Exact visible text / element | Type, dynamic source | Interaction/calculation | Verification |
|---|---|---|---|
| `AI Demand Forecast` | Title, line 11 | Static | AppTest rendered |
| `Explore the trained model’s current daily demand estimate and compare it with clearly labelled demonstration data.` | Caption, line 11 | Static | AppTest rendered |
| Prediction unavailable error | Conditional; lines 12–13 | Displays `prediction_error` or fallback | Source inspected, branch not forced |
| `Current model prediction` | Metric, two decimals units/day; help says four named shared inputs; line 15 | V2 inference, base prediction | AppTest rendered |
| Current scenario adjustment caption | Shows percentage and adjusted units/day; line 16 | Shared demand multiplier; separate from inventory measurement | AppTest rendered |
| `Demand history and weekday shape` | Header; line 18 | Static | AppTest rendered |
| Synthetic demand trend | Date / Demand (units/day), markers, dashed annotation `Current model prediction`; lines 19–24 | Default Plotly hover uses date/value; synthetic generator; no custom hover template or controls | AppTest rendered |
| Synthetic weekday bar chart | Weekday / Mean synthetic demand; fixed Mon–Sun order; teal bars; lines 25–32 | Default Plotly hover uses weekday/value; mean of 30 synthetic visual values grouped by date weekday | AppTest rendered |
| No observed demand history disclosure | Caption; line 33 | Separates visual series from notebook training/evaluation CSV | AppTest rendered |
| `Notebook-reported benchmark MAE (synthetic holdout)` | Header; line 35 | Static; benchmark reference values | AppTest rendered |
| MAE bar chart | Categories `Previous-day baseline`, `V2 model`; text labels 2.31 and 2.09; axis `Benchmark MAE (units/day; lower is better)`; lines 36–39 | Default Plotly hover shows category/value; values are notebook-reported literals, not loaded dynamically | AppTest regression confirms labels; evaluator independently reproduced |
| Evaluation info | Identifies fixed synthetic benchmarks, current evaluator command, and no real-world accuracy claim; line 41 | Static | AppTest rendered |

## Page 4 — Scenario Simulator

Source: `pages/4_Scenario_Simulator.py`.

| Exact visible text / element | Type, default/range | Interaction/calculation | Verification |
|---|---|---|---|
| `Scenario Simulator` | Title, line 11 | Static | AppTest rendered |
| `Run a hypothetical planning case and see how demand, lead time, capacity, stock, and safety stock affect replenishment.` | Caption, line 11 | Static | AppTest rendered |
| Prediction failure message | Error then stop; lines 12–14 | Conditional if base prediction unavailable | Branch inspected, not forced |
| Form | `scenario_form`; lines 16–24 | Inputs apply on `Apply scenario` submit; controls have independent `sim_*` keys | AppTest submit tested |
| `Scenario demand change (%)` | Slider, -50..100, initialized from shared demand change; key `sim_change`; line 18 | Scenario multiplier of base model prediction | AppTest changed to +50%, demand/ROP/order changed |
| `Scenario supplier lead time (days)` | Slider, 1..30, shared lead default; key `sim_lead`; line 19 | Reorder input | AppTest changed to 8, ROP changed |
| `Scenario capacity (units)` | Number input, min 10, max 10000, initial shared capacity; key `sim_capacity`; line 20 | Scales hypothetical stock from scenario percentage | AppTest changed to 200, suggested order changed |
| `Scenario inventory (%)` | Slider, 0..100, initial rounded shared fill; key `sim_inventory_pct`; line 22 | Converts capacity to scenario stock | AppTest changed to 20%, order changed |
| `Scenario safety stock (units)` | Number input 0..10000, shared initial; key `sim_safety`; line 23 | ROP addition | AppTest changed to 40, ROP changed |
| `Apply scenario` | Primary form submit button; line 24 | Submits values and reruns calculations | AppTest button submit exercised |
| `Baseline vs. hypothetical scenario` | Header; line 35 | Static | AppTest rendered |
| Comparison table | Measures: Demand (units/day), Reorder point (units), Suggested order (units), Days of stock; Baseline/Scenario columns; lines 36–42 | Baseline from shared calculations; scenario from form values | AppTest rendered; data source inspected |
| Five scenario metrics | `Adjusted demand`, `Reorder point`, `Suggested replenishment`, `Estimated days of stock`, `Reorder threshold`; lines 43–49 | Displays values/status, threshold `Reached` iff scenario stock <= ROP | AppTest base and parameter changes verified |
| Demand comparison chart | Baseline and scenario traces; y-axis `Demand (units/day)` | Same demand comparison as the table, displayed separately from inventory quantities | AppTest asserts units and baseline/scenario traces |
| Inventory comparison chart | Baseline and scenario traces; categories Reorder point and Current stock; y-axis `Inventory (units)` | Compares like-unit inventory quantities without placing demand on this axis | AppTest asserts units and baseline/scenario traces |
| Scenario summary | Dynamic delta text for demand/ROP/order; line 57 | Compares against shared baseline | AppTest rendered |
| Hypothetical data caveat | Caption; line 58 | Baseline uses sidebar; units derive from percentage × capacity | AppTest rendered |

## Page 5 — Replenishment & Alerts

Source: `pages/5_Replenishment_Alerts.py`.

| Exact visible text / element | Type, dynamic source | Interaction/calculation | Verification |
|---|---|---|---|
| `Replenishment & Alerts` | Title, line 10 | Static | AppTest rendered |
| `Translate the inventory estimate and demand plan into a clear, reviewable replenishment recommendation.` | Caption, line 10 | Static | AppTest rendered |
| Demand error | Error then stop; lines 11–13 | Conditional if prediction unavailable | Branch inspected only |
| `Current estimated stock` | Metric, one decimal units; line 16 | Shared inventory estimate | AppTest rendered 49.1 |
| `Reorder point` | Metric, one decimal units; line 17 | Shared ROP | AppTest rendered 86.4 |
| `Suggested order` | Metric, integer units; line 18 | Shared ceiling order | AppTest rendered 38 |
| `Lead time` | Metric, days; line 19 | Shared control | AppTest rendered 3 days |
| `Safety stock` | Metric, units; line 20 | Shared control | AppTest rendered 10 units |
| Urgency warning | `Urgent` or `Plan now`; line 23 | When stock <= ROP; Urgent iff stock <= safety stock, otherwise Plan now | Default plan-now branch rendered |
| Monitor success | Text says no immediate reorder when stock > ROP; line 26 | Conditional | Source inspected, branch not forced |
| Reorder calculation/non-action caveat | Caption gives demand × lead + safety stock = ROP; disclaims exact package count/volume and order/supplier action; line 27 | Static values interpolated from shared calculations | AppTest rendered |
| `Replenishment planning` | Header; line 29 | Static | AppTest rendered |
| Planning table | Columns: `As of`, `Source`, `Estimated stock (units)`, `Adjusted demand (units/day)`, `Lead time (days)`, `Safety stock (units)`, `Reorder point (units)`, `Suggested order (units)`, `Urgency`; lines 30–36 | One row from same `table` DataFrame used by exporter | AppTest rendered table; values exposed in AppTest DataFrame |
| `Download recommendation CSV` | Primary download button; `replenishment_recommendation.csv`, UTF-8 CSV; line 37 | Downloads current planning table; no order is placed | AppTest rendered button/URL; actual file transfer/content not tested in browser |

## Page 6 — System Health & Model Insights

Source: `pages/6_System_Health.py`.

| Exact visible text / element | Type, dynamic source | Interaction/calculation | Verification |
|---|---|---|---|
| `System Health & Model Insights` | Title, line 8 | Static | AppTest rendered |
| `Check model availability, data provenance, validation, and the current integration boundary.` | Caption, line 8 | Static | AppTest rendered |
| `Data mode` | Metric; line 11 | Simulated or Live Sensor | AppTest rendered simulated |
| `Sensor connection` | Metric; line 12 | Explicit service state | AppTest rendered |
| `Model file` | Metric Available/Missing and Loaded/Not loaded; line 13 | Model status helper | AppTest loaded V2 |
| Live sensor success details | Port, baud, timestamp, distance; lines 14–16 | Conditional on Live Sensor | Source inspected; hardware branch not forced |
| Hardware-state simulation info | No verified live reading / simulated distance / port scan disclaimer; line 18 | Conditional if not Live Sensor | AppTest rendered; no hardware |
| `Model details` | Header; line 20 | Static | AppTest rendered |
| Loaded model estimator/path | Success text; line 22 | Dynamic model metadata | AppTest rendered |
| `Required input feature order` | Text; line 23 | Values from loaded artifact metadata or expected features | Model feature order inspected and loaded |
| Compatibility warnings / no warnings | Dynamic warnings or `No model loading warnings were reported.`; lines 24–27 | Depends on sklearn/joblib loading | Current env no warnings |
| Missing model error | Error; line 29 | Conditional when unavailable | Source inspected only |
| Prediction validation explanation | Text about named finite input and negative output clipping; line 30 | Static | AppTest rendered |
| `Data quality and available evaluation` | Header; line 32 | Static | AppTest rendered |
| Demand input validity | Dynamic valid/invalid; line 33 | `prediction_error` state | AppTest rendered valid |
| Distance calibration validity | Dynamic valid/invalid fallback; line 34 | Shared calibration | AppTest rendered valid |
| Demand history provenance | Text distinguishes no observed history and synthetic demo series; line 35 | Static | AppTest rendered |
| Evaluation provenance and metrics | Text states synthetic V2/baseline MAE and command; line 36 | Static values, evaluator separately run | AppTest rendered; evaluator reproduced metrics |
| Sensor-history retention | Text says latest reading in-memory only and history synthetic; line 37 | Static | AppTest rendered |
| `System workflow` | Header; lines 39–48 | Static technical explanation | AppTest rendered |
| Workflow step 1: `Shared sidebar values provide the scenario inputs and four demand-model features.` | Markdown ordered-list item; line 41 | Static | AppTest rendered |
| Workflow step 2: `The preserved demand_model_v2.joblib predicts daily demand; inventory measurement is a separate calculation.` | Markdown ordered-list item; line 42 | Static | AppTest rendered |
| Workflow step 3: `A side-mounted distance to the package surface is converted through the calibrated distance target and empty-box baseline. The target is not proof that the box is physically full. A live value is used only after a recent valid serial reading; otherwise simulation is used.` | Markdown ordered-list item; line 43 | Static | AppTest rendered |
| Workflow step 4: `Adjusted daily demand, supplier lead time, and safety stock produce the reorder point.` | Markdown ordered-list item; line 44 | Static | AppTest rendered |
| Workflow step 5: `Suggested replenishment is the non-negative ceiling of reorder point minus estimated stock.` | Markdown ordered-list item; line 45 | Static | AppTest rendered |
| `Serial readings are managed by one cached background service. Demand forecasting remains separate from inventory measurement.` | Closing markdown paragraph; line 47 | Static | AppTest rendered |

## Unavailable/absent element types

No file uploader, editable table, date picker, user text input, tab set, external-link action, or database form was found in active app/page source. The scenario page has one form; sidebar controls are ordinary Streamlit widgets. Tooltips are present on Overview Days of stock and Forecast current model prediction. Conditional error/status branches exist but some were not forced during AppTest.

## Interaction verification limits

AppTest confirms the six scripts render without Streamlit exceptions and permits mocked control changes. It does not prove CSS appearance at projector resolution, keyboard accessibility, chart tooltip behavior in a browser, serial device ownership on macOS, or download transfer integrity. The first AppTest download-probe command attempted an unsupported property while inspecting the test harness; the app page itself rendered and the supported `download_button` element was subsequently confirmed. No browser or physical hardware verification is claimed.
