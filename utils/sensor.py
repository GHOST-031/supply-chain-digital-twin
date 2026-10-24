"""Threaded, process-wide serial service for optional ultrasonic readings.

The module does not open ports on import. A port is opened only after an
explicit connect action or when the UI sees exactly one USB serial candidate.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import atexit
import re
import threading
import time
from typing import Callable, Optional

import streamlit as st


DEFAULT_BAUD_RATE = 115200
MIN_VALID_DISTANCE_CM = 2.0
MAX_VALID_DISTANCE_CM = 400.0
DEFAULT_STALE_AFTER_SECONDS = 5.0
DEFAULT_FIRST_READING_TIMEOUT_SECONDS = 15.0
DEFAULT_READ_TIMEOUT_SECONDS = 0.25

SIMULATED = "Simulated"
CONNECTING = "Connecting"
LIVE_SENSOR = "Live Sensor"
DISCONNECTED_ERROR = "Disconnected/Error"

_DISTANCE_LINE = re.compile(
    r"^\s*Distance:\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*cm\s*$",
    re.IGNORECASE,
)


class SensorParseError(ValueError):
    """A serial line did not contain a plausible distance measurement."""


class NoEchoError(SensorParseError):
    """The firmware reports that the ultrasonic sensor received no echo."""


class SerialUnavailableError(RuntimeError):
    """pyserial is unavailable or serial-port enumeration failed."""


@dataclass(frozen=True)
class SensorReading:
    distance_cm: float
    timestamp: str
    source: str = "live"


@dataclass(frozen=True)
class SerialPortInfo:
    device: str
    description: str = ""
    hwid: str = ""
    vid: Optional[int] = None
    pid: Optional[int] = None

    @property
    def label(self) -> str:
        detail = self.description or self.hwid
        return f"{self.device} — {detail}" if detail else self.device


def parse_distance_line(line: bytes | str) -> float:
    """Parse the project's firmware format and reject nonphysical values."""
    if isinstance(line, bytes):
        try:
            text = line.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise SensorParseError("Serial line is not valid UTF-8.") from exc
    else:
        text = str(line)
    text = text.strip()
    if not text:
        raise SensorParseError("Empty serial line.")
    if text.casefold() == "no echo detected":
        raise NoEchoError("Firmware reports: No echo detected.")
    match = _DISTANCE_LINE.fullmatch(text)
    if not match:
        raise SensorParseError("Expected a line such as 'Distance: 24.5 cm'.")
    distance = float(match.group(1))
    if not MIN_VALID_DISTANCE_CM <= distance <= MAX_VALID_DISTANCE_CM:
        raise SensorParseError(
            f"Distance {distance:g} cm is outside the valid HC-SR04 range "
            f"({MIN_VALID_DISTANCE_CM:g}–{MAX_VALID_DISTANCE_CM:g} cm)."
        )
    return distance


def list_serial_ports() -> list[SerialPortInfo]:
    """Enumerate ports through pyserial without opening any of them."""
    try:
        from serial.tools import list_ports
    except ImportError as exc:
        raise SerialUnavailableError(
            "pyserial is not installed. Run `pip install -r requirements.txt`."
        ) from exc
    try:
        return [
            SerialPortInfo(
                device=port.device,
                description=port.description or "",
                hwid=port.hwid or "",
                vid=getattr(port, "vid", None),
                pid=getattr(port, "pid", None),
            )
            for port in list_ports.comports()
        ]
    except Exception as exc:
        raise SerialUnavailableError(f"Could not enumerate serial ports: {exc}") from exc


def is_usb_serial_candidate(port: SerialPortInfo) -> bool:
    """Recognize common USB serial devices without choosing arbitrary ports."""
    device = port.device.casefold()
    mac_prefixes = (
        "/dev/cu.usbserial-",
        "/dev/cu.wchusbserial",
        "/dev/cu.slab_usbtouart",
        "/dev/cu.usbmodem",
        "/dev/tty.usbserial-",
        "/dev/tty.wchusbserial",
        "/dev/tty.slab_usbtouart",
        "/dev/tty.usbmodem",
    )
    if device.startswith(mac_prefixes):
        return True
    if device.startswith(("/dev/ttyusb", "/dev/ttyacm")):
        return True
    description = f"{port.description} {port.hwid}".casefold()
    usb_serial_terms = ("usb", "serial", "uart", "ch340", "cp210", "ftdi", "wch")
    return port.vid is not None or any(term in description for term in usb_serial_terms)


class SensorService:
    """One background reader, at most one open port, safe across reruns.

    Inject ``serial_factory`` and ``ports_provider`` to exercise the service
    without hardware. Reader threads never call Streamlit APIs.
    """

    def __init__(
        self,
        serial_factory: Optional[Callable] = None,
        ports_provider: Optional[Callable[[], list[SerialPortInfo]]] = None,
        stale_after_seconds: float = DEFAULT_STALE_AFTER_SECONDS,
        first_read_timeout_seconds: float = DEFAULT_FIRST_READING_TIMEOUT_SECONDS,
        read_timeout_seconds: float = DEFAULT_READ_TIMEOUT_SECONDS,
    ):
        self._serial_factory = serial_factory
        self._ports_provider = ports_provider or list_serial_ports
        self.stale_after_seconds = float(stale_after_seconds)
        self.first_read_timeout_seconds = float(first_read_timeout_seconds)
        self.read_timeout_seconds = float(read_timeout_seconds)
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._serial = None
        self._generation = 0
        self._connect_started = 0.0
        self._last_valid_monotonic: Optional[float] = None
        self._latest_reading: Optional[SensorReading] = None
        self._last_auto_attempt: Optional[str] = None
        self._state = SIMULATED
        self._status_message = "No verified live reading. Simulation is active."
        self._last_error: Optional[str] = None
        self._port: Optional[str] = None
        self._baud_rate = DEFAULT_BAUD_RATE

    def available_ports(self) -> list[SerialPortInfo]:
        return list(self._ports_provider())

    @property
    def last_auto_attempt(self) -> Optional[str]:
        with self._lock:
            return self._last_auto_attempt

    def clear_auto_attempt(self) -> None:
        with self._lock:
            self._last_auto_attempt = None

    def auto_connect_unique(self, ports: list[SerialPortInfo], baud_rate: int = DEFAULT_BAUD_RATE) -> bool:
        """Open a port automatically only when exactly one USB candidate exists."""
        candidates = [port for port in ports if is_usb_serial_candidate(port)]
        if len(candidates) != 1:
            return False
        candidate = candidates[0]
        with self._lock:
            if self._state in (CONNECTING, LIVE_SENSOR) or self._last_auto_attempt == candidate.device:
                return False
        return self.start(candidate.device, baud_rate, automatic=True)

    def start(self, port: str, baud_rate: int = DEFAULT_BAUD_RATE, *, automatic: bool = False) -> bool:
        """Start a reader thread and return immediately; live needs a valid line."""
        port = str(port).strip()
        baud_rate = int(baud_rate)
        if not port:
            self._set_error("Select a serial port before connecting.")
            return False
        if baud_rate <= 0:
            self._set_error("Baud rate must be a positive integer.")
            return False
        with self._lock:
            if self._state in (CONNECTING, LIVE_SENSOR):
                if self._port == port:
                    return True
                self._last_error = "Disconnect the active port before selecting another port."
                self._status_message = self._last_error
                return False
            if self._thread is not None and self._thread.is_alive():
                self._last_error = "The previous serial reader is still shutting down. Try again shortly."
                self._status_message = self._last_error
                return False
            self._generation += 1
            generation = self._generation
            self._stop_event = threading.Event()
            self._connect_started = time.monotonic()
            self._last_valid_monotonic = None
            self._latest_reading = None
            self._state = CONNECTING
            self._port = port
            self._baud_rate = baud_rate
            self._last_error = None
            self._status_message = "Opening serial port; waiting for a valid sensor reading."
            if automatic:
                self._last_auto_attempt = port
            self._thread = threading.Thread(
                target=self._reader_loop,
                args=(generation, port, baud_rate, self._stop_event),
                name=f"supply-chain-digital-twin-serial-{generation}",
                daemon=True,
            )
            self._thread.start()
            return True

    def disconnect(self, *, use_simulation: bool = False, message: Optional[str] = None) -> None:
        """Stop the reader and immediately make all inventory use simulation."""
        with self._lock:
            self._generation += 1
            self._stop_event.set()
            serial_handle = self._serial
            self._serial = None
            self._latest_reading = None
            self._last_valid_monotonic = None
            self._state = SIMULATED if use_simulation else DISCONNECTED_ERROR
            if use_simulation:
                self._last_error = None
                self._status_message = message or "Simulation selected by user."
            else:
                self._last_error = message or "Serial connection disconnected by user."
                self._status_message = self._last_error
        self._close_serial(serial_handle)
        thread = self._thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=max(0.1, self.read_timeout_seconds + 0.2))

    def use_simulation(self) -> None:
        self.disconnect(use_simulation=True)

    def snapshot(self) -> dict:
        """Return a thread-safe state snapshot, expiring stale live readings."""
        serial_to_close = None
        with self._lock:
            now = time.monotonic()
            age = None if self._last_valid_monotonic is None else max(0.0, now - self._last_valid_monotonic)
            if self._state == LIVE_SENSOR and age is not None and age > self.stale_after_seconds:
                self._state = DISCONNECTED_ERROR
                self._last_error = f"Sensor reading is stale ({age:.1f}s old; limit {self.stale_after_seconds:.1f}s)."
                self._status_message = self._last_error + " Inventory has returned to simulation."
                self._stop_event.set()
                serial_to_close = self._serial
                self._serial = None
                self._last_valid_monotonic = None
                age = None
            reading = self._latest_reading
            result = {
                "state": self._state,
                "mode": LIVE_SENSOR if self._state == LIVE_SENSOR else SIMULATED,
                "port": self._port,
                "baud_rate": self._baud_rate,
                "reading": reading,
                "reading_age_seconds": age,
                "last_error": self._last_error,
                "status_message": self._status_message,
                "has_verified_reading": self._state == LIVE_SENSOR and reading is not None,
            }
        self._close_serial(serial_to_close)
        return result

    def _set_error(self, message: str) -> None:
        with self._lock:
            self._state = DISCONNECTED_ERROR
            self._last_error = message
            self._status_message = message + " Inventory is using simulation."

    def _make_serial(self, port: str, baud_rate: int):
        if self._serial_factory is not None:
            return self._serial_factory(port, baudrate=baud_rate, timeout=self.read_timeout_seconds)
        try:
            import serial
        except ImportError as exc:
            raise SerialUnavailableError(
                "pyserial is not installed. Run `pip install -r requirements.txt`."
            ) from exc
        return serial.Serial(port, baudrate=baud_rate, timeout=self.read_timeout_seconds)

    def _reader_loop(self, generation: int, port: str, baud_rate: int, stop_event: threading.Event) -> None:
        serial_handle = None
        try:
            serial_handle = self._make_serial(port, baud_rate)
            with self._lock:
                if generation != self._generation or stop_event.is_set():
                    return
                self._serial = serial_handle
                self._status_message = "Serial port opened; waiting for a valid distance line."
            while not stop_event.is_set():
                try:
                    line = serial_handle.readline()
                except Exception as exc:
                    self._mark_reader_error(generation, f"Serial read failed: {exc}")
                    break
                if line:
                    try:
                        distance = parse_distance_line(line)
                    except NoEchoError as exc:
                        self._set_message_if_current(generation, str(exc))
                    except SensorParseError as exc:
                        self._set_message_if_current(generation, f"Ignored invalid sensor line: {exc}")
                    else:
                        self._accept_reading(generation, distance)
                if self._check_timeout(generation):
                    break
                if getattr(serial_handle, "is_open", True) is False:
                    self._mark_reader_error(generation, "Serial device closed unexpectedly.")
                    break
        except Exception as exc:
            self._mark_reader_error(generation, f"Could not open {port}: {exc}")
        finally:
            self._close_serial(serial_handle)
            with self._lock:
                if self._serial is serial_handle:
                    self._serial = None
                if generation == self._generation and self._state in (CONNECTING, LIVE_SENSOR) and not stop_event.is_set():
                    self._state = DISCONNECTED_ERROR
                    self._last_error = "Serial reader stopped unexpectedly."
                    self._status_message = self._last_error + " Inventory has returned to simulation."

    def _accept_reading(self, generation: int, distance: float) -> None:
        with self._lock:
            if generation != self._generation or self._stop_event.is_set():
                return
            now = time.monotonic()
            self._last_valid_monotonic = now
            self._latest_reading = SensorReading(
                distance_cm=distance,
                timestamp=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            )
            self._state = LIVE_SENSOR
            self._last_error = None
            self._status_message = "Valid, recent ultrasonic distance received."

    def _check_timeout(self, generation: int) -> bool:
        with self._lock:
            if generation != self._generation or self._stop_event.is_set():
                return True
            now = time.monotonic()
            if self._state == CONNECTING and now - self._connect_started > self.first_read_timeout_seconds:
                message = "No valid sensor reading arrived before the connection timeout."
            elif self._state == LIVE_SENSOR and self._last_valid_monotonic is not None and now - self._last_valid_monotonic > self.stale_after_seconds:
                message = "Sensor readings became stale; device may be disconnected or returning no echo."
            else:
                return False
            self._state = DISCONNECTED_ERROR
            self._last_error = message
            self._status_message = message + " Inventory has returned to simulation."
            self._stop_event.set()
            return True

    def _set_message_if_current(self, generation: int, message: str) -> None:
        with self._lock:
            if generation == self._generation and not self._stop_event.is_set():
                self._status_message = message

    def _mark_reader_error(self, generation: int, message: str) -> None:
        with self._lock:
            if generation == self._generation:
                self._state = DISCONNECTED_ERROR
                self._last_error = message
                self._status_message = message + " Inventory has returned to simulation."
                self._stop_event.set()

    @staticmethod
    def _close_serial(serial_handle) -> None:
        if serial_handle is None:
            return
        try:
            cancel_read = getattr(serial_handle, "cancel_read", None)
            if callable(cancel_read):
                cancel_read()
        except Exception:
            pass
        try:
            serial_handle.close()
        except Exception:
            pass


@st.cache_resource(show_spinner=False)
def get_sensor_service() -> SensorService:
    """Return one process-wide port owner shared across pages and reruns."""
    service = SensorService()
    atexit.register(service.use_simulation)
    return service
