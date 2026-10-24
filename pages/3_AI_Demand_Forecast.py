import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.simulation import synthetic_history
from utils.state import refresh_pages_when_sensor_changes
from utils.ui import COLORS, page_header, shared_data

refresh_pages_when_sensor_changes()
d = shared_data()
page_header("AI Demand Forecast", "Explore the trained model’s current daily demand estimate and compare it with clearly labelled demonstration data.")
if d["predicted_demand"] is None:
    st.error(d["prediction_error"] or "Demand prediction is unavailable.")
else:
    st.metric("Current model prediction", f"{d['predicted_demand']:.2f} units/day", help="Prediction uses the four named inputs shown in the shared sidebar controls.")
    st.caption(f"Current scenario adjustment: {d['demand_change']:+d}% → {d['scenario_demand']:.2f} units/day. Demand forecast is separate from inventory measurement.")

st.subheader("Demand history and weekday shape")
history = synthetic_history()
left, right = st.columns(2)
fig = px.line(history, x="date", y="demand_units", markers=True, labels={"date":"Date", "demand_units":"Demand (units/day)"})
if d["predicted_demand"] is not None: fig.add_hline(y=d["predicted_demand"], line_dash="dash", line_color=COLORS["amber"], annotation_text="Current model prediction")
fig.update_layout(template="plotly_white", height=320, margin=dict(l=20,r=20,t=20,b=20))
left.plotly_chart(fig, width="stretch")
history["weekday"] = history.date.dt.day_name()
pattern = history.groupby("weekday", as_index=False).demand_units.mean()
order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
pattern["weekday"] = __import__("pandas").Categorical(pattern.weekday, categories=order, ordered=True)
pattern = pattern.sort_values("weekday")
fig2 = px.bar(pattern, x="weekday", y="demand_units", labels={"weekday":"Weekday", "demand_units":"Mean synthetic demand"}, color_discrete_sequence=[COLORS["teal"]])
fig2.update_layout(template="plotly_white", height=320, margin=dict(l=20,r=20,t=20,b=20), showlegend=False)
right.plotly_chart(fig2, width="stretch")
st.caption("No observed demand history is present. These trend and weekday charts use reproducible synthetic demonstration data, separate from the notebook-derived synthetic training/evaluation dataset.")

# These are notebook-reported reference values; evaluation remains a separate workflow.
st.subheader("Notebook-reported benchmark MAE (synthetic holdout)")
base_mae, model_mae = 2.31, 2.09
fig3 = go.Figure(go.Bar(x=["Previous-day baseline", "V2 model"], y=[base_mae, model_mae], text=[f"{base_mae:.2f}", f"{model_mae:.2f}"], textposition="outside", marker_color=["#91a3b5", COLORS["blue"]]))
fig3.update_layout(template="plotly_white", height=300, yaxis_title="Benchmark MAE (units/day; lower is better)", margin=dict(l=20,r=20,t=20,b=20), showlegend=False)
st.plotly_chart(fig3, width="stretch")
st.info("Fixed reference values reported by the training notebook: V2 MAE 2.09 units/day and previous-day baseline MAE 2.31 units/day on synthetic data. This page does not evaluate artifacts at runtime; run `python training/evaluate_models.py` to recompute metrics from the current saved models and `training/synthetic_demand.csv`. Synthetic results are not evidence of real-world warehouse forecasting accuracy.")
