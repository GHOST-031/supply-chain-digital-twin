from datetime import date
import pandas as pd
import streamlit as st

from utils.ui import page_header, shared_data
from utils.state import refresh_pages_when_sensor_changes

refresh_pages_when_sensor_changes()
d=shared_data()
page_header("Replenishment & Alerts", "Translate the inventory estimate and demand plan into a clear, reviewable replenishment recommendation.")
if d["predicted_demand"] is None:
    st.error("Recommendation unavailable because demand prediction failed.")
    st.stop()
stock, rop, order = d["stock"], d["reorder_point"], d["suggested_order"]
cols=st.columns(5)
cols[0].metric("Current estimated stock",f"{stock:.1f} units")
cols[1].metric("Reorder point",f"{rop:.1f} units")
cols[2].metric("Suggested order",f"{order} units")
cols[3].metric("Lead time",f"{d['lead_time']} days")
cols[4].metric("Safety stock",f"{d['safety_stock']} units")
if stock <= rop:
    urgency="Urgent" if stock <= d["safety_stock"] else "Plan now"
    st.warning(f"{urgency}: estimated stock is {max(0, rop-stock):.1f} units below the reorder point. Suggested quantity is {order} units to bring estimated stock up to the reorder point.")
else:
    urgency="Monitor"
    st.success(f"No immediate reorder is indicated. Estimated stock is {stock-rop:.1f} units above the reorder point; monitor demand and supplier lead time.")
st.caption(f"Calculation: reorder point = {d['scenario_demand']:.2f} units/day × {d['lead_time']} days + {d['safety_stock']} safety-stock units = {rop:.2f} units. Inventory units are capacity-scaled from the calibrated occupancy estimate, not an exact package count or physical volume. This is a planning recommendation only; no order is placed and no supplier is contacted.")

st.subheader("Replenishment planning")
table=pd.DataFrame([{
    "As of":date.today().isoformat(),"Source":f"{d['inventory_source']} inventory + model demand",
    "Estimated stock (units)":round(stock,1),"Adjusted demand (units/day)":round(d["scenario_demand"],2),
    "Lead time (days)":d["lead_time"],"Safety stock (units)":d["safety_stock"],
    "Reorder point (units)":round(rop,2),"Suggested order (units)":order,"Urgency":urgency,
}])
st.dataframe(table,hide_index=True,width="stretch")
st.download_button("Download recommendation CSV",table.to_csv(index=False).encode("utf-8"),file_name="replenishment_recommendation.csv",mime="text/csv",type="primary")
