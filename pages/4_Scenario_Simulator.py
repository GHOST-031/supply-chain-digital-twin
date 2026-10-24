import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.inventory import calculate_stock, days_of_stock, reorder_point, suggested_order
from utils.state import refresh_pages_when_sensor_changes
from utils.ui import COLORS, page_header, shared_data

refresh_pages_when_sensor_changes()
d = shared_data()
page_header("Scenario Simulator", "Run a hypothetical planning case and see how demand, lead time, capacity, stock, and safety stock affect replenishment.")
if d["predicted_demand"] is None:
    st.error("Scenario analysis requires a valid demand prediction. Check the model inputs and model status.")
    st.stop()
base = d["predicted_demand"]
with st.form("scenario_form"):
    c1,c2,c3 = st.columns(3)
    change = c1.slider("Scenario demand change (%)", -50, 100, d["demand_change"], key="sim_change")
    lead = c2.slider("Scenario supplier lead time (days)", 1, 30, d["lead_time"], key="sim_lead")
    capacity = c3.number_input("Scenario capacity (units)", 10, 10000, int(d["capacity"]), key="sim_capacity")
    c4,c5 = st.columns(2)
    inventory_pct = c4.slider("Scenario inventory (%)", 0, 100, int(round(d["fill_percent"])), key="sim_inventory_pct")
    safety = c5.number_input("Scenario safety stock (units)", 0, 10000, int(d["safety_stock"]), key="sim_safety")
    submitted = st.form_submit_button("Apply scenario", type="primary")

# Form values update on submission; defaults remain aligned to current shared inputs.
scenario_demand = max(0.0, base * (1 + change / 100))
scenario_stock = calculate_stock(capacity, inventory_pct)
scenario_rop = reorder_point(scenario_demand, lead, safety)
scenario_order = suggested_order(scenario_stock, scenario_rop)
scenario_days = days_of_stock(scenario_stock, scenario_demand)
baseline_order = d["suggested_order"]
baseline_days = days_of_stock(d["stock"], d["scenario_demand"])

st.subheader("Baseline vs. hypothetical scenario")
comparison = pd.DataFrame([
    {"Measure":"Demand (units/day)","Baseline":d["scenario_demand"],"Scenario":scenario_demand},
    {"Measure":"Reorder point (units)","Baseline":d["reorder_point"],"Scenario":scenario_rop},
    {"Measure":"Suggested order (units)","Baseline":baseline_order,"Scenario":scenario_order},
    {"Measure":"Days of stock","Baseline":baseline_days,"Scenario":scenario_days},
])
st.dataframe(comparison, hide_index=True, width="stretch", column_config={"Baseline":st.column_config.NumberColumn(format="%.1f"),"Scenario":st.column_config.NumberColumn(format="%.1f")})
metrics=st.columns(5)
metrics[0].metric("Adjusted demand",f"{scenario_demand:.1f} units/day",f"{change:+d}%")
metrics[1].metric("Reorder point",f"{scenario_rop:.1f} units",f"Lead time {lead} days")
metrics[2].metric("Suggested replenishment",f"{scenario_order} units")
metrics[3].metric("Estimated days of stock",f"{scenario_days:.1f}" if scenario_days is not None else "—")
reorder_threshold_reached = scenario_stock <= scenario_rop
metrics[4].metric("Reorder threshold", "Reached" if reorder_threshold_reached else "Not reached", "Stock at/below reorder point" if reorder_threshold_reached else "Stock above reorder point")

demand_col, inventory_col = st.columns(2)
with demand_col:
    st.subheader("Daily demand (units/day)")
    demand_fig = go.Figure(go.Bar(
        x=["Baseline", "Scenario"],
        y=[d["scenario_demand"], scenario_demand],
        marker_color=["#91a3b5", COLORS["blue"]],
    ))
    demand_fig.update_layout(
        template="plotly_white", height=340, yaxis_title="Demand (units/day)",
        showlegend=False, margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(demand_fig, width="stretch")

with inventory_col:
    st.subheader("Inventory quantities (units)")
    inventory_fig = go.Figure()
    inventory_fig.add_trace(go.Bar(
        name="Baseline", x=["Reorder point", "Current stock"],
        y=[d["reorder_point"], d["stock"]], marker_color="#91a3b5",
    ))
    inventory_fig.add_trace(go.Bar(
        name="Scenario", x=["Reorder point", "Current stock"],
        y=[scenario_rop, scenario_stock], marker_color=COLORS["blue"],
    ))
    inventory_fig.update_layout(
        barmode="group", template="plotly_white", height=340,
        yaxis_title="Inventory (units)", margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(inventory_fig, width="stretch")
delta_order=scenario_order-(baseline_order or 0)
st.write(f"**Scenario summary:** adjusted demand changes by {scenario_demand-d['scenario_demand']:+.1f} units/day, the reorder point by {scenario_rop-d['reorder_point']:+.1f} units, and the suggested order by {delta_order:+d} units versus baseline.")
st.caption("Scenario figures are hypothetical. Baseline uses the shared sidebar settings; inventory units are derived from the scenario percentage and capacity.")
