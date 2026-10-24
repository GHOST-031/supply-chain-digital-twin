import plotly.graph_objects as go
import streamlit as st

from utils.inventory import days_of_stock
from utils.simulation import synthetic_history, synthetic_inventory_history
from utils.state import refresh_pages_when_sensor_changes
from utils.ui import COLORS, page_header, shared_data

refresh_pages_when_sensor_changes()
d = shared_data()
page_header("Executive Overview", "A concise view of estimated inventory, demand pressure, and the next replenishment decision.")
if not d:
    st.error("Shared application inputs are not available. Return to the main app and reload.")
    st.stop()
cols = st.columns(5)
cols[0].metric("Estimated stock", f"{d['stock']:.0f} units", f"{d['fill_percent']:.0f}% of capacity")
cols[1].metric("Base model prediction", f"{d['predicted_demand']:.1f} units/day" if d["predicted_demand"] is not None else "Unavailable")
cols[2].metric("Reorder point", f"{d['reorder_point']:.1f} units" if d["reorder_point"] is not None else "Unavailable")
cols[3].metric("Suggested replenishment", f"{d['suggested_order']} units" if d["suggested_order"] is not None else "Unavailable")
days = days_of_stock(d["stock"], d["scenario_demand"]) if d["scenario_demand"] is not None else None
cols[4].metric("Days of stock", f"{days:.1f} days" if days is not None else "—", help="Unavailable when daily demand is zero or could not be predicted.")
if d["scenario_demand"] is not None:
    st.caption(
        f"Planning demand: {d['scenario_demand']:.1f} units/day after the "
        f"{d['demand_change']:+d}% shared demand adjustment. This adjusted value "
        "is used for the reorder point and days-of-stock calculation."
    )

if d["inventory_status"] == "Critical":
    st.error(f"Inventory health: {d['inventory_status']}. Review supply availability and plan an urgent replenishment.")
elif d["inventory_status"] == "Reorder required":
    st.warning(f"Inventory health: {d['inventory_status']}. Estimated stock is at or below the calculated reorder point.")
elif d["inventory_status"] == "Low":
    st.warning("Inventory health: Low. The container is at or below 30% full.")
else:
    st.success(f"Inventory health: {d['inventory_status']}. Stock is above the current reorder threshold.")
st.info(f"Sensor mode: **{d['sensor_mode']}**. Inventory source: **{d['inventory_source']}**.")
if d["prediction_error"]:
    st.error(f"Demand prediction unavailable: {d['prediction_error']}")

st.subheader("Recent demand and estimated inventory")
left, right = st.columns(2)
demand = synthetic_history()
stock = synthetic_inventory_history(d["stock"], d["capacity"])
fig = go.Figure()
fig.add_trace(go.Scatter(x=demand.date, y=demand.demand_units, mode="lines", name="Synthetic demand", line={"color": COLORS["blue"], "width": 2}))
fig.add_hline(y=d["predicted_demand"] or 0, line_dash="dash", line_color=COLORS["amber"], annotation_text="Current model prediction")
fig.update_layout(height=320, template="plotly_white", yaxis_title="Units / day", margin=dict(l=20,r=20,t=20,b=20), legend=dict(orientation="h", y=1.1))
left.plotly_chart(fig, width="stretch")
fig2 = go.Figure(go.Scatter(x=stock.date, y=stock.stock_units, mode="lines+markers", name="Simulated stock", line={"color": COLORS["teal"], "width": 2}, fill="tozeroy", fillcolor="rgba(28,154,138,.10)"))
fig2.add_hline(y=d["reorder_point"] or 0, line_dash="dash", line_color=COLORS["red"], annotation_text="Reorder point")
fig2.update_layout(height=320, template="plotly_white", yaxis_title="Estimated units", margin=dict(l=20,r=20,t=20,b=20), showlegend=False)
right.plotly_chart(fig2, width="stretch")
st.caption(f"Both history series are reproducible synthetic demonstrations. Current inventory uses {d['inventory_source'].lower()} distance; demand comes from the trained model.")
