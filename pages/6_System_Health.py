import streamlit as st

from utils.ui import page_header, shared_data
from utils.state import refresh_pages_when_sensor_changes

refresh_pages_when_sensor_changes()
d=shared_data()
page_header("System Health & Model Insights", "Check model availability, data provenance, validation, and the current integration boundary.")
model=d["model_status"]
c1,c2,c3=st.columns(3)
c1.metric("Data mode",d["sensor_mode"])
c2.metric("Sensor connection",d["sensor_state"])
c3.metric("Model file","Available" if model["available"] else "Missing","Loaded" if model["loaded"] else "Not loaded")
if d["sensor_mode"] == "Live Sensor":
    st.success(f"A recent valid distance is being received from {d['sensor']['port']} at {d['sensor']['baud_rate']} baud.")
    st.write(f"Latest accepted reading (UTC): {d['sensor_reading_timestamp']} — {d['sensor']['reading'].distance_cm:.1f} cm.")
else:
    st.info("Hardware state: no verified live reading is available. Inventory uses the simulated distance. Ports are scanned, but a detected port alone does not count as a sensor connection.")

st.subheader("Model details")
if model["loaded"]:
    st.success(f"Loaded {model['estimator']} from `{model['path']}`.")
    st.write("**Required input feature order:** " + ", ".join(model["features"]))
    if model["warnings"]:
        for warning in model["warnings"]: st.warning(f"Model compatibility notice: {warning}")
    else:
        st.write("No model loading warnings were reported.")
else:
    st.error(model["error"] or "Model is unavailable.")
st.write("Prediction validates named, finite inputs and clips a negative model output to zero. The trained artifact is preserved and is not retrained by this app.")

st.subheader("Data quality and available evaluation")
st.write("**Demand inputs:** " + ("valid" if not d["prediction_error"] else "invalid / unavailable"))
st.write("**Distance calibration:** " + ("valid" if d["calibration_valid"] else "invalid range; container-bound fallback used"))
st.write("**Demand history:** no observed demand history is present; forecast trend and weekday charts use reproducible synthetic demonstration data, separate from the notebook-derived synthetic training/evaluation dataset.")
st.write("**Evaluation benchmark:** the UI shows fixed notebook-reported values (V2 MAE 2.09 units/day; previous-day baseline MAE 2.31 units/day). Run `python training/evaluate_models.py` to recompute metrics from the current saved models and synthetic CSV. These synthetic results are not evidence of real-world warehouse forecasting accuracy.")
st.write("**Sensor history:** only the latest in-memory reading is retained; historical inventory charts remain synthetic and no readings are persisted.")

st.subheader("System workflow")
st.markdown("""
1. Shared sidebar values provide the scenario inputs and four demand-model features.
2. The preserved `demand_model_v2.joblib` predicts daily demand; inventory measurement is a separate calculation.
3. A side-mounted distance to the package surface is converted through the calibrated distance target and empty-box baseline. The target is not proof that the box is physically full. A live value is used only after a recent valid serial reading; otherwise simulation is used.
4. Adjusted daily demand, supplier lead time, and safety stock produce the reorder point.
5. Suggested replenishment is the non-negative ceiling of reorder point minus estimated stock.

Serial readings are managed by one cached background service. Demand forecasting remains separate from inventory measurement.
""")
