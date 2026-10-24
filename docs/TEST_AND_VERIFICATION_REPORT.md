# Test and Verification Report

**Run date:** 2026-10-23. This report includes the read-only audit and targeted UI/documentation fixes. Checks used the project `.venv`; no packages were installed, no dataset was written, no training was performed, and no model artifact was replaced.

## Targeted follow-up

The side-mounted sensor wording is corrected in active UI/setup text. The scenario comparison now renders separate demand (`units/day`) and inventory (`units`) charts. Container height is documented as a simulation fallback input when explicit calibration endpoints are invalid; with the configured valid 30.9 cm empty baseline and 2.6 cm target, it does not alter the calibrated interpolation. The forecast page labels 2.09 and 2.31 as fixed notebook-reported synthetic benchmarks, not runtime evaluation or real-world accuracy.

Regression coverage was added for valid-calibration independence from container height, fallback behavior, scenario chart units/comparison traces, benchmark disclosure, and CSV values matching the displayed replenishment table.

## Results

| Test/check | Expected | Actual | Result | Evidence / scope |
|---|---|---|---|---|
| Existing unit suite and follow-up regressions: `PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m unittest discover -s tests -v` | All discovered tests pass | 27 tests, 0 failures/errors, exit 0, 2.339 s | PASS | Includes sensor parser/service, calibration and inventory, six-page AppTest, scenario charts, forecast disclosure, and CSV/table equality |
| Python compile check: `PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -c 'from pathlib import Path; import ast; files=[p for p in Path(".").rglob("*.py") if ".venv" not in p.parts and "backups" not in p.parts and "__pycache__" not in p.parts]; [ast.parse(p.read_text(),filename=str(p)) for p in files]; print(f"Compiled {len(files)} active Python files successfully")'` | No syntax errors | `Compiled 19 active Python files successfully`, exit 0 | PASS | In-memory parse/compile check; excluded archived backups and `.venv` |
| Evaluation: `PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B training/evaluate_models.py` | Existing artifacts load and compute metrics on same chronological test rows | Exit 0; 358 rows, 286 train / 72 test; V1 2.2236285197; V2 2.0868998601; baseline 2.3055555556; rounded 2.22 / 2.09 / 2.31 | PASS | Script loads artifacts only; no fit or save, as confirmed by its output/source |
| Dataset generator parity | Generated values equal saved CSV without writing | Called `generate_dataset()` in memory; `DataFrame.equals(existing_csv)` True, shape 358×6 | PASS | No generator CLI was run; existing CSV preserved |
| Artifact identity | Both artifacts remain present/intact during evaluation | V1 SHA-256 `5fd83cf96e32fc914262ffbed5f35f538f5fbd421fe832fe206d128405b90105`; V2 `943ecc0c522dfdac82c838d5ba4042ce4339d5e9e16b4e6372ebf04d4c817889`; values matched in pre/post evaluation checks | PASS | Model files were never written by this audit |
| Model loading and inference | App V2 loads with current expected features and returns valid prediction | `LinearRegression`, loaded True, warnings `[]`, feature order V2 correct; input (22,20,21,4) -> 21.2140966405 units/day | PASS | Current environment sklearn 1.6.1 matches requirements pin; inference test also passed |
| Calibration independent check | Endpoints and supplied intermediates match formula | 30.9→0%; 2.6→100%; 16.2→51.9434628975%; 15.7→53.7102473498%; 12.7→64.3109540636% | PASS | In-memory direct function invocation; unit tests also cover endpoints, midpoint, clamps and invalid inputs |
| Calibration default AppTest | Fresh app session exposes intended defaults | 2.6 cm target and 30.9 cm empty baseline | PASS | AppTest from `app.py`; no application exception |
| Six-page Streamlit AppTest | Every registered page renders without exception | Re-run after changes: landing page and all six page switches had zero exceptions | PASS | Auto-connect mocked off to prevent host serial access. This is Streamlit AppTest, not browser automation |
| Scenario input behavior | Every scenario control changes expected derived KPI after submit | Demand +50% changed demand 25.5→31.8; lead 3→8 changed ROP 86.4→213.7; capacity 100→200 changed order 38→0; stock 49→20% changed order 38→67; safety 10→40 changed ROP 86.4→116.4 | PASS | AppTest submits form after setting each key; separate fresh app instance per case |
| Shared default KPI chain | Overview and planning values are coherent | AppTest displayed base 21.2, adjusted 25.5, fill/stock 49.1, ROP 86.4, order 38, days 1.9; alerts displayed the same detailed stock/ROP/order | PASS | AppTest observed values; independent arithmetic documented in KPI reference |
| CSV export consistency | Exported recommendation equals visible planning table | Regression test captures download payload and asserts DataFrame equality with rendered table | PASS (AppTest payload) | Browser-triggered download still not verified; see NOT VERIFIED items |
| Browser interaction / visual appearance | Actual rendered site and all controls exercised | No supported local browser automation was available | NOT RUN | AppTest must not be treated as browser E2E |
| Physical ESP8266 + HC-SR04 | Firmware upload, electrical wiring, serial data and physical calibration work | No device was connected or tested | NOT RUN | Mock serial tests are not hardware evidence |

## Test case inventory

The 23 sensor/model unittest cases, plus four targeted frontend regressions, report `ok` (27 total):

- `ExistingCalculationRegressionTests`: calibration endpoints/clamping; measured calibration endpoints/intermediate; measured-range clamping; invalid calibration/finite distance; stock/reorder/order regression; valid live calibrated reading; invalid live calibration simulation fallback; current model prediction.
- `SensorParsingTests`: common USB serial port detection; plausible and non-finite value rejection; malformed lines; `No echo detected`; valid distance format.
- `SensorServiceTests`: ambiguous ports; unique auto-connect remains simulated until valid reading; first-reading timeout; disconnect after live; immediate manual simulation; unavailable port; no duplicate active port; read exception; stale reading fallback.
- `FrontendRegressionTests`: scenario charts separate demand and inventory units; fixed synthetic benchmark disclosure; exported recommendation CSV equals the displayed table.
- `FrontendRegressionTests`: all six registered pages render without Streamlit exceptions.

The new container-height test additionally proves that valid explicit endpoints dominate the calculation and that container height remains relevant to the invalid-calibration fallback. Existing defaults were kept at 30.9 cm and 2.6 cm.

## AppTest coverage performed

Fresh `AppTest.from_file("app.py")` checked no initial exception and showed the current default calibration values. `switch_page` was used on each page path:

1. `pages/1_Executive_Overview.py`
2. `pages/2_Inventory_Digital_Twin.py`
3. `pages/3_AI_Demand_Forecast.py`
4. `pages/4_Scenario_Simulator.py`
5. `pages/5_Replenishment_Alerts.py`
6. `pages/6_System_Health.py`

All rendered without page exceptions. The scenario form was submitted with each of its five controls varied individually. AppTest emitted Streamlit's usual `missing ScriptRunContext` warning in bare mode; it did not produce page exceptions. One early inspection command mistakenly asked AppTest for a nonexistent `navigation` attribute and another attempted a non-existent test-element field; these were harness introspection errors, not application failures. The checks were rerun using supported page switching and element APIs.

## Not run / limitations

- No browser, screen-size, projector, keyboard-navigation, hover-tooltip, or actual file-download verification.
- No serial hardware or firmware compiler/IDE test, and no electrical validation.
- No tests of concurrent browser sessions sharing the process-wide sensor service.
- No `pytest` suite was present/configured; project tests use `unittest` discovery.
- The evaluation script was run on the existing CSV; its dataset-writing CLI was intentionally not run.
- No dependency install/clean-environment install was attempted.

## Model and dataset integrity

`training/evaluate_models.py` was run against the committed-in-workspace CSV and model files. It explicitly prints that it loaded artifacts and did not fit/save. SHA-256 values before and after this evaluation matched; V2 remains the artifact loaded by the app. No metric claim here is a real-world accuracy claim.
