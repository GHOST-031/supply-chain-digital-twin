import plotly.graph_objects as go
import streamlit as st

from utils.simulation import synthetic_inventory_history
from utils.state import refresh_pages_when_sensor_changes
from utils.ui import COLORS, page_header, shared_data

refresh_pages_when_sensor_changes()
d = shared_data()
page_header("Inventory Digital Twin", "Convert a side-mounted ultrasonic distance reading toward the packages into a calibrated occupancy estimate.")
st.caption(f"Current inventory source: {d['inventory_source']}. A live value is used only after a recent valid serial reading and valid calibration.")
col1, col2, col3 = st.columns(3)
col1.metric("Storage capacity", f"{d['capacity']} units")
col2.metric("Container height", f"{d['container_height']} cm")
col3.metric("Sensor to stock surface", f"{d['distance_cm']:.1f} cm")

fill = d["fill_percent"]
stock = d["stock"]
left, right = st.columns([1, 1.4])
with left:
    st.subheader("Estimated Fill / Occupancy (%)")
    fig = go.Figure(go.Bar(x=["Estimated Fill / Occupancy"], y=[fill], marker_color=COLORS["teal"], text=[f"{fill:.0f}%"], textposition="inside"))
    fig.update_layout(height=340, template="plotly_white", yaxis={"title":"Fill", "range":[0,100], "ticksuffix":"%"}, showlegend=False, margin=dict(l=25,r=25,t=20,b=25))
    st.plotly_chart(fig, width="stretch")
    st.progress(fill / 100)
with right:
    st.subheader("Estimated inventory")
    st.metric("Capacity-scaled inventory estimate", f"{stock:.1f} units", f"{fill:.1f}% occupancy estimate")
    st.write(f"**Reading status:** {d['sensor_status']}  ")
    st.write(f"**Calibration range:** full-distance target {d['valid_min_distance']:.1f} cm; empty-box baseline {d['valid_max_distance']:.1f} cm. The mapped estimate is clamped to 0–100%.")
    st.caption("The target endpoint is a calibration reference and does not mean the box is physically full unless validated experimentally.")
    st.write("A smaller surface gap means a higher estimated stock level. Values outside the calibrated range are clamped to full or empty.")
    st.caption("Calibration is specific to the demonstrated package arrangement. Occupancy is a distance-based estimate, not true physical volume or an exact package count; estimated units scale this percentage by configured capacity, and replenishment uses that estimate.")
    if not d["calibration_valid"]:
        st.warning("Calibration range is invalid because the empty-level distance must exceed the full-level distance. Container bounds were used for this estimate.")
    if d["inventory_status"] == "Critical": st.error("Critical: nearly empty or empty.")
    elif d["inventory_status"] == "Reorder required": st.warning("Estimated stock is at or below the reorder point.")
    elif d["inventory_status"] == "Low": st.warning("Low fill: at or below 30%.")
    else: st.success("Inventory level is healthy against the current thresholds.")

st.subheader("Demonstration inventory history")
hist = synthetic_inventory_history(stock, d["capacity"])
fig = go.Figure(go.Scatter(x=hist.date, y=hist.stock_units, mode="lines+markers", name="Simulated stock", line={"color":COLORS["blue"]}, fill="tozeroy", fillcolor="rgba(40,120,181,.10)"))
if d["reorder_point"] is not None:
    fig.add_hline(
        y=d["reorder_point"], line_dash="dash", line_color=COLORS["red"],
        annotation_text="Reorder point",
    )
fig.update_layout(height=300, template="plotly_white", yaxis_title="Estimated units", margin=dict(l=20,r=20,t=20,b=20))
st.plotly_chart(fig, width="stretch")
st.caption("The history is generated for demonstration and ends at the current estimate. It is not a recorded sensor history, even when the current endpoint comes from a live reading.")
