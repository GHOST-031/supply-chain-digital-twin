"""Supply Chain Digital Twin: multi-page Streamlit entry point."""
from datetime import date

import streamlit as st

from utils.inventory import is_valid_distance_calibration
from utils.sensor import (
    CONNECTING,
    DEFAULT_BAUD_RATE,
    DISCONNECTED_ERROR,
    LIVE_SENSOR,
    SIMULATED,
    SerialUnavailableError,
    get_sensor_service,
    is_usb_serial_candidate,
)
from utils.state import refresh_shared_data

st.set_page_config(page_title="Supply Chain Digital Twin", layout="wide")

st.markdown("""
<style>
  .block-container {padding-top: 1.6rem; padding-bottom: 2.5rem;}
  [data-testid="stMetric"] {background:#f5f8fc; border:1px solid #e3eaf3; padding:16px 18px; border-radius:12px;}
  [data-testid="stMetricLabel"] p {color:#53657a; font-weight:600;}
  h1, h2, h3 {letter-spacing:-.02em;}
  .status-pill {display:inline-block; padding:5px 10px; border-radius:20px; background:#e8f2ff; color:#175aa6; font-size:.82rem; font-weight:650;}
</style>
""", unsafe_allow_html=True)

st.sidebar.title("Supply Chain Digital Twin")
st.sidebar.caption("Inventory monitoring · demand planning")
st.sidebar.markdown("---")
st.sidebar.subheader("Shared planning inputs")
st.sidebar.caption("These controls update the figures across all pages.")
st.sidebar.number_input("Storage capacity (units)", 10, 1000, 100, key="capacity")
st.sidebar.slider(
    "Container height (cm)", 10, 200, 50, key="container_height",
    help="Used for container-bound simulation fallback when calibration endpoints are invalid. With valid explicit endpoints, those distances determine the occupancy estimate.",
)
st.sidebar.number_input("Calibrated full-distance target (cm)", 0.0, 200.0, 2.6, key="valid_min_distance")
st.sidebar.number_input("Empty-box baseline distance (cm)", 0.1, 200.0, 30.9, key="valid_max_distance")
st.sidebar.caption("The full-distance value is a calibration target; it does not establish that the box is physically full unless validated experimentally.")
st.sidebar.slider("Simulated sensor distance (cm)", 0, 200, 17, key="distance_cm")
st.sidebar.slider("Demand change (%)", -50, 100, 20, key="demand_change")
st.sidebar.slider("Supplier lead time (days)", 1, 30, 3, key="lead_time")
st.sidebar.number_input("Safety stock (units)", 0, 10000, 10, key="safety_stock")
with st.sidebar.expander("Demand model inputs"):
    st.number_input("Previous day demand", 0.0, 10000.0, 22.0, key="previous_day")
    st.number_input("Previous week demand", 0.0, 10000.0, 20.0, key="previous_week")
    st.number_input("7-day rolling average", 0.0, 10000.0, 21.0, key="rolling_avg")
    st.selectbox("Day of week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], index=date.today().weekday(), key="weekday")
st.sidebar.markdown("---")
st.sidebar.subheader("Ultrasonic sensor")


@st.fragment(run_every=1.0)
def render_sensor_controls():
    service = get_sensor_service()
    baud_rate = st.sidebar.number_input(
        "Serial baud rate", min_value=1200, max_value=1000000,
        value=DEFAULT_BAUD_RATE, step=1200, key="sensor_baud_rate",
    )
    automatic_detection = st.sidebar.checkbox(
        "Auto-connect when one USB serial device is found", value=True,
        key="sensor_auto_connect",
    )
    refresh_clicked = st.sidebar.button("Refresh serial ports", key="refresh_sensor_ports")
    if refresh_clicked:
        service.clear_auto_attempt()
    try:
        ports = service.available_ports()
        port_error = None
    except SerialUnavailableError as exc:
        ports = []
        port_error = str(exc)

    candidates = [port for port in ports if is_usb_serial_candidate(port)]
    status = service.snapshot()
    if automatic_detection and len(candidates) == 1 and status["state"] in (SIMULATED, DISCONNECTED_ERROR):
        service.auto_connect_unique(ports, int(baud_rate))
        status = service.snapshot()

    if automatic_detection and len(candidates) > 1:
        st.sidebar.warning("Multiple USB serial devices found. Choose a port and connect manually.")
    labels = [port.label for port in ports]
    if labels:
        selected_label = st.sidebar.selectbox("Serial port", labels, key="sensor_port_choice")
        selected_port = ports[labels.index(selected_label)].device
    else:
        st.sidebar.selectbox("Serial port", ["No serial ports detected"], disabled=True, key="sensor_port_choice_empty")
        selected_port = None

    connect_col, disconnect_col = st.sidebar.columns(2)
    connect_feedback = None
    if connect_col.button("Connect", key="connect_sensor", disabled=selected_port is None):
        if not service.start(selected_port, int(baud_rate)):
            connect_feedback = service.snapshot()["last_error"]
    if disconnect_col.button("Disconnect", key="disconnect_sensor", disabled=status["state"] not in (CONNECTING, LIVE_SENSOR)):
        service.disconnect()
    if st.sidebar.button("Switch to simulation", key="switch_sensor_simulation", disabled=status["state"] == SIMULATED):
        service.use_simulation()

    status = service.snapshot()
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Shared sensor status**")
    st.sidebar.write(f"**Mode:** {status['mode']}  ")
    st.sidebar.write(f"**Connection:** {status['state']}")
    st.sidebar.write(f"**Port:** {status['port'] or 'Not selected'} · **Baud:** {status['baud_rate']}")
    reading = status["reading"]
    if reading is not None:
        age = status["reading_age_seconds"]
        age_text = f"{age:.1f}s ago" if age is not None else "stale"
        st.sidebar.write(f"**Latest valid distance:** {reading.distance_cm:.1f} cm")
        st.sidebar.caption(f"Received (UTC): {reading.timestamp} · age {age_text}")
    else:
        st.sidebar.write("**Latest valid distance:** —")
    full_distance = st.session_state.valid_min_distance
    empty_distance = st.session_state.valid_max_distance
    if not is_valid_distance_calibration(full_distance, empty_distance):
        st.sidebar.error("Calibration invalid: empty-bin distance must exceed full-bin distance.")
    else:
        st.sidebar.caption(f"Calibration: full {full_distance:g} cm · empty {empty_distance:g} cm")
    if status["state"] == SIMULATED:
        st.sidebar.info("Simulation is active. A detected port alone does not enable live mode.")
    elif status["state"] == CONNECTING:
        st.sidebar.info("Connecting; waiting for a valid distance reading.")
    elif status["state"] == LIVE_SENSOR:
        st.sidebar.success("Live mode uses recent validated serial readings.")
    else:
        st.sidebar.warning(status["status_message"])
    if connect_feedback:
        st.sidebar.error(connect_feedback)

    current_data = refresh_shared_data()
    st.sidebar.metric(
        f"{current_data['inventory_source']} calibrated fill",
        f"{current_data['fill_percent']:.1f}%",
    )
    if status["state"] == LIVE_SENSOR and not current_data["calibration_valid"]:
        st.sidebar.warning("Live distance is available, but inventory remains simulated until calibration is valid.")
    if port_error:
        st.sidebar.error(port_error)
        st.sidebar.caption("Install the project dependencies, reconnect the board, and refresh ports. Close Arduino Serial Monitor first.")
    elif not ports:
        st.sidebar.caption("No serial ports detected. Check the USB cable/driver, then refresh. Close other serial monitor apps.")


render_sensor_controls()

PAGES = [
    st.Page("pages/1_Executive_Overview.py", title="Executive Overview", default=True),
    st.Page("pages/2_Inventory_Digital_Twin.py", title="Inventory Digital Twin"),
    st.Page("pages/3_AI_Demand_Forecast.py", title="AI Demand Forecast"),
    st.Page("pages/4_Scenario_Simulator.py", title="Scenario Simulator"),
    st.Page("pages/5_Replenishment_Alerts.py", title="Replenishment & Alerts"),
    st.Page("pages/6_System_Health.py", title="System Health & Model Insights"),
]
navigation = st.navigation(PAGES, position="sidebar")

refresh_shared_data()

navigation.run()
