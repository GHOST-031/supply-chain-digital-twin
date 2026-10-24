# ESP8266 + HC-SR04 setup

This app supports an optional serial sensor feed. The demonstrated HC-SR04 is mounted horizontally through the side of the box and measures distance toward the packages in its beam. Simulation remains the fallback, and the dashboard changes inventory to live data only after it receives a recent, validated `Distance: ... cm` line. Finding a USB port alone does not establish a live sensor.

## 1. Install and run the dashboard on macOS

From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

If the project already has a usable `.venv`, activate it and run the dependency install and launch commands without recreating it.

## 2. Upload the firmware

Open `firmware/esp8266_hcsr04.ino` in Arduino IDE, select the correct ESP8266 NodeMCU board and USB serial port, then upload it. The sketch uses `Serial.begin(115200)` and emits readings such as `Distance: 24.5 cm`; it emits `No echo detected` when `pulseIn` times out. Its assumed pins are documented and configurable at the top of the sketch; confirm the pins against your actual board and wiring before use.

**Electrical caution:** many HC-SR04 modules drive ECHO at 5 V, while ESP8266 GPIO inputs are 3.3 V. Use a suitable level shifter or resistor divider for ECHO and verify the board/module requirements. This software does not make an unsafe electrical connection safe.

## 3. Find the serial port and connect

In Terminal, inspect likely macOS device names:

```bash
ls /dev/cu.*
```

Common examples include `/dev/cu.usbserial-*`, `/dev/cu.wchusbserial*`, and `/dev/cu.SLAB_USBtoUART*`. The app scans serial ports without opening them. If exactly one USB serial candidate is present and automatic detection is enabled, it attempts that port. It remains in Connecting until a valid reading arrives. If multiple candidates appear, select the intended port in the sidebar and choose Connect.

Close Arduino Serial Monitor and any other terminal/serial program before connecting from Streamlit. Typically, only one process can own the serial port at a time. Use **Refresh serial ports** after attaching the board. The baud-rate default is 115200.

## 4. Calibrate the container

For this side-mounted setup, measure the sensor-to-package-surface distance with the box empty and with the demonstrated reference package arrangement. Enter 30.9 cm as the empty-box baseline and use 2.6 cm as the calibrated full-distance target in the shared sidebar. The target is a mapping endpoint only; it does not establish that the box is physically full unless that state has been validated experimentally. Use the same centimetre units as the firmware. Smaller distance maps to a higher estimated occupancy only for arrangements that produce a consistent reflection in the sensor beam.

The app maps the target distance to 100% estimated fill/occupancy and the empty baseline to 0%, clamps out-of-range readings, and multiplies the percentage by configured capacity. This is not a true volume estimate or an exact package count. Invalid calibration is shown as a warning; the live distance may be visible, but inventory remains simulated until calibration is valid.

`Container height (cm)` is used for the container-bound simulation fallback when calibration endpoints are invalid. With valid explicit endpoints (the normal configured case), the empty baseline and target distance determine the interpolation, so changing container height does not change the occupancy calculation.

## 5. Verify live mode

The sidebar should show **Live Sensor** only after a valid recent reading has been parsed. It displays the selected port, baud rate, distance, UTC timestamp/age, and calibrated fill. Inventory, stock status, and replenishment update across pages. If data stops for more than five seconds, the app reports Disconnected/Error and uses the simulation distance again. Choose **Switch to simulation** to return manually.

Troubleshooting: verify the USB cable supports data, select the correct board/port in Arduino IDE, close Serial Monitor, confirm 115200 baud, check the ECHO voltage interface and pin wiring, then refresh the port list. “No echo detected” and malformed lines do not activate live mode.

## Testing without hardware

The tests use a mocked serial reader and do not open a real port. From the project directory, run:

```bash
python -m unittest discover -s tests -v
```

No physical ESP8266/HC-SR04 test is claimed by this project change.
