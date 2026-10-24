import queue
import time
import unittest

from utils.inventory import (
    calculate_stock,
    fill_from_distance,
    is_valid_distance_calibration,
    reorder_point,
    suggested_order,
)
from utils.state import estimate_inventory
from utils.simulation import get_simulated_reading
from utils.sensor import (
    CONNECTING,
    DEFAULT_BAUD_RATE,
    DISCONNECTED_ERROR,
    LIVE_SENSOR,
    SIMULATED,
    NoEchoError,
    SerialPortInfo,
    SensorParseError,
    SensorReading,
    SensorService,
    is_usb_serial_candidate,
    parse_distance_line,
)


class FakeSerial:
    def __init__(self, port, baudrate, timeout):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.lines = queue.Queue()
        self.is_open = True
        self.raise_on_read = False
        self.close_count = 0

    def readline(self):
        if self.raise_on_read:
            raise OSError("mock device disconnected")
        try:
            value = self.lines.get(timeout=self.timeout)
        except queue.Empty:
            return b""
        if isinstance(value, Exception):
            raise value
        return value

    def cancel_read(self):
        pass

    def close(self):
        self.close_count += 1
        self.is_open = False


class SensorParsingTests(unittest.TestCase):
    def test_valid_distance_line(self):
        self.assertEqual(parse_distance_line(b"Distance: 24.5 cm\r\n"), 24.5)
        self.assertEqual(parse_distance_line(" distance: 2 cm "), 2.0)

    def test_no_echo_is_a_specific_non_measurement(self):
        with self.assertRaises(NoEchoError):
            parse_distance_line("No echo detected\r\n")

    def test_malformed_lines_are_rejected(self):
        for line in (b"", "starting sensor", "Distance = 24 cm", "Distance: 24 inches", b"\xff"):
            with self.subTest(line=line), self.assertRaises(SensorParseError):
                parse_distance_line(line)

    def test_implausible_and_nonfinite_distances_are_rejected(self):
        for line in ("Distance: 1.9 cm", "Distance: 400.1 cm", "Distance: nan cm", "Distance: inf cm"):
            with self.subTest(line=line), self.assertRaises(SensorParseError):
                parse_distance_line(line)

    def test_common_usb_serial_port_detection(self):
        for device in (
            "/dev/cu.usbserial-1420",
            "/dev/cu.wchusbserial1410",
            "/dev/cu.SLAB_USBtoUART",
            "/dev/ttyUSB0",
            "/dev/ttyACM0",
        ):
            with self.subTest(device=device):
                self.assertTrue(is_usb_serial_candidate(SerialPortInfo(device)))
        self.assertFalse(is_usb_serial_candidate(SerialPortInfo("/dev/cu.Bluetooth-Incoming-Port")))
        self.assertTrue(is_usb_serial_candidate(SerialPortInfo("COM7", "USB Serial Device")))


class SensorServiceTests(unittest.TestCase):
    def setUp(self):
        self.created = []

        def factory(port, baudrate, timeout):
            reader = FakeSerial(port, baudrate, timeout)
            self.created.append(reader)
            return reader

        self.service = SensorService(
            serial_factory=factory,
            ports_provider=lambda: [],
            stale_after_seconds=0.18,
            first_read_timeout_seconds=0.5,
            read_timeout_seconds=0.02,
        )

    def tearDown(self):
        self.service.use_simulation()

    def wait_until(self, condition, timeout=1.5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if condition():
                return True
            time.sleep(0.01)
        return bool(condition())

    def wait_for_reader(self):
        self.assertTrue(self.wait_until(lambda: bool(self.created)), "reader did not open")
        return self.created[0]

    def test_automatic_unique_port_stays_simulated_until_valid_reading(self):
        candidate = SerialPortInfo("/dev/cu.usbserial-demo", "USB Serial")
        self.assertTrue(self.service.auto_connect_unique([candidate]))
        self.assertEqual(self.service.snapshot()["state"], CONNECTING)
        self.assertEqual(self.service.snapshot()["mode"], SIMULATED)
        self.assertEqual(self.service.snapshot()["baud_rate"], DEFAULT_BAUD_RATE)

        reader = self.wait_for_reader()
        reader.lines.put(b"No echo detected\n")
        reader.lines.put(b"startup text\n")
        time.sleep(0.05)
        self.assertEqual(self.service.snapshot()["state"], CONNECTING)
        self.assertEqual(self.service.snapshot()["mode"], SIMULATED)

        reader.lines.put(b"Distance: 24.5 cm\n")
        self.assertTrue(self.wait_until(lambda: self.service.snapshot()["state"] == LIVE_SENSOR))
        snapshot = self.service.snapshot()
        self.assertEqual(snapshot["mode"], LIVE_SENSOR)
        self.assertEqual(snapshot["reading"].distance_cm, 24.5)
        self.assertIsNotNone(snapshot["reading"].timestamp)

    def test_ambiguous_ports_do_not_auto_connect(self):
        ports = [
            SerialPortInfo("/dev/cu.usbserial-a"),
            SerialPortInfo("/dev/cu.SLAB_USBtoUART"),
        ]
        self.assertFalse(self.service.auto_connect_unique(ports))
        self.assertEqual(self.service.snapshot()["state"], SIMULATED)
        self.assertEqual(self.created, [])

    def test_port_unavailable_is_reported_and_falls_back(self):
        service = SensorService(
            serial_factory=lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError("port unavailable")),
            read_timeout_seconds=0.01,
        )
        try:
            self.assertTrue(service.start("/dev/cu.missing", 115200))
            self.assertTrue(self.wait_until(lambda: service.snapshot()["state"] == DISCONNECTED_ERROR))
            snapshot = service.snapshot()
            self.assertEqual(snapshot["mode"], SIMULATED)
            self.assertIn("port unavailable", snapshot["last_error"])
        finally:
            service.use_simulation()

    def test_connection_times_out_without_a_valid_first_reading(self):
        service = SensorService(
            serial_factory=lambda port, baudrate, timeout: FakeSerial(port, baudrate, timeout),
            first_read_timeout_seconds=0.06,
            stale_after_seconds=0.2,
            read_timeout_seconds=0.01,
        )
        try:
            service.start("COM8", 115200)
            self.assertTrue(self.wait_until(lambda: service.snapshot()["state"] == DISCONNECTED_ERROR))
            self.assertEqual(service.snapshot()["mode"], SIMULATED)
            self.assertIn("connection timeout", service.snapshot()["last_error"])
        finally:
            service.use_simulation()

    def test_serial_read_exception_disconnects_and_falls_back(self):
        self.assertTrue(self.service.start("COM7", 115200))
        reader = self.wait_for_reader()
        reader.raise_on_read = True
        self.assertTrue(self.wait_until(lambda: self.service.snapshot()["state"] == DISCONNECTED_ERROR))
        self.assertEqual(self.service.snapshot()["mode"], SIMULATED)

    def test_disconnect_after_live_reading_returns_to_simulation(self):
        self.service.start("COM7", 115200)
        reader = self.wait_for_reader()
        reader.lines.put(b"Distance: 22.0 cm\n")
        self.assertTrue(self.wait_until(lambda: self.service.snapshot()["state"] == LIVE_SENSOR))
        reader.raise_on_read = True
        self.assertTrue(self.wait_until(lambda: self.service.snapshot()["state"] == DISCONNECTED_ERROR))
        self.assertEqual(self.service.snapshot()["mode"], SIMULATED)

    def test_stale_reading_returns_to_simulated_mode(self):
        self.service.start("COM7", 115200)
        reader = self.wait_for_reader()
        reader.lines.put(b"Distance: 30.0 cm\n")
        self.assertTrue(self.wait_until(lambda: self.service.snapshot()["state"] == LIVE_SENSOR))
        self.assertTrue(self.wait_until(lambda: self.service.snapshot()["state"] == DISCONNECTED_ERROR, timeout=1.0))
        snapshot = self.service.snapshot()
        self.assertEqual(snapshot["mode"], SIMULATED)
        self.assertIn("stale", snapshot["status_message"].lower())

    def test_same_active_port_is_not_opened_twice(self):
        self.assertTrue(self.service.start("COM7", 115200))
        self.wait_for_reader()
        self.assertTrue(self.service.start("COM7", 115200))
        self.assertEqual(len(self.created), 1)

    def test_disconnect_switches_immediately_to_simulation(self):
        self.service.start("COM7", 115200)
        reader = self.wait_for_reader()
        reader.lines.put(b"Distance: 22.0 cm\n")
        self.assertTrue(self.wait_until(lambda: self.service.snapshot()["state"] == LIVE_SENSOR))
        self.service.use_simulation()
        self.assertEqual(self.service.snapshot()["state"], SIMULATED)
        self.assertIsNone(self.service.snapshot()["reading"])


class ExistingCalculationRegressionTests(unittest.TestCase):
    def test_calibration_boundaries_and_clamping(self):
        self.assertEqual(fill_from_distance(50, 0, 0, 50), 100)
        self.assertEqual(fill_from_distance(50, 25, 0, 50), 50)
        self.assertEqual(fill_from_distance(50, 50, 0, 50), 0)
        self.assertEqual(fill_from_distance(50, -10, 0, 50), 100)
        self.assertEqual(fill_from_distance(50, 80, 0, 50), 0)

    def test_measured_package_calibration_endpoints_and_intermediate(self):
        self.assertEqual(fill_from_distance(10.2, 30.9, 2.6, 30.9), 0)
        self.assertEqual(fill_from_distance(10.2, 2.6, 2.6, 30.9), 100)
        self.assertAlmostEqual(fill_from_distance(10.2, 16.75, 2.6, 30.9), 50)
        self.assertAlmostEqual(fill_from_distance(10.2, 20.0, 2.6, 30.9), 38.5159010601)

    def test_measured_package_calibration_clamps_out_of_range_readings(self):
        self.assertEqual(fill_from_distance(10.2, 35.0, 2.6, 30.9), 0)
        self.assertEqual(fill_from_distance(10.2, 1.0, 2.6, 30.9), 100)

    def test_container_height_is_only_used_for_invalid_calibration_fallback(self):
        calibrated_at_small_height = fill_from_distance(10.2, 16.2, 2.6, 30.9)
        calibrated_at_large_height = fill_from_distance(100.0, 16.2, 2.6, 30.9)
        self.assertEqual(calibrated_at_small_height, calibrated_at_large_height)

        fallback_at_50_cm = get_simulated_reading(25.0, 50.0, 100, 30.0, 20.0)
        fallback_at_100_cm = get_simulated_reading(25.0, 100.0, 100, 30.0, 20.0)
        self.assertFalse(fallback_at_50_cm["calibration_valid"])
        self.assertFalse(fallback_at_100_cm["calibration_valid"])
        self.assertEqual(fallback_at_50_cm["fill_percent"], 50)
        self.assertEqual(fallback_at_100_cm["fill_percent"], 75)

    def test_invalid_calibration_is_rejected_without_division_by_zero(self):
        invalid_ranges = (
            (30.9, 30.9),
            (30.9, 2.6),
            (-1.0, 30.9),
            (2.6, float("nan")),
            (2.6, float("inf")),
            (None, 30.9),
            ("invalid", 30.9),
        )
        for full_distance, empty_distance in invalid_ranges:
            with self.subTest(full=full_distance, empty=empty_distance):
                self.assertFalse(is_valid_distance_calibration(full_distance, empty_distance))
                with self.assertRaises(ValueError):
                    fill_from_distance(10.2, 20.0, full_distance, empty_distance)
        self.assertFalse(is_valid_distance_calibration(2.6, None))
        with self.assertRaises(ValueError):
            fill_from_distance(10.2, float("nan"), 2.6, 30.9)

    def test_inventory_and_replenishment_logic_is_preserved(self):
        self.assertEqual(calculate_stock(100, 50), 50)
        self.assertEqual(reorder_point(10, 5, 7), 57)
        self.assertEqual(suggested_order(50, 57), 7)
        self.assertEqual(suggested_order(60, 57), 0)

    def test_live_inventory_uses_valid_calibrated_reading(self):
        snapshot = {
            "mode": LIVE_SENSOR,
            "reading": SensorReading(25.0, "2026-01-01T00:00:00+00:00"),
        }
        inventory = estimate_inventory(snapshot, 200, 50, 17, 0, 50)
        self.assertEqual(inventory["inventory_source"], LIVE_SENSOR)
        self.assertEqual(inventory["fill_percent"], 50)
        self.assertEqual(inventory["stock"], 100)

    def test_invalid_live_calibration_keeps_inventory_simulated(self):
        snapshot = {
            "mode": LIVE_SENSOR,
            "reading": SensorReading(25.0, "2026-01-01T00:00:00+00:00"),
        }
        inventory = estimate_inventory(snapshot, 100, 50, 17, 30, 20)
        self.assertEqual(inventory["inventory_source"], "Simulation")
        self.assertFalse(inventory["calibration_valid"])
        self.assertEqual(inventory["fill_percent"], 66)

    def test_existing_demand_model_still_predicts(self):
        from utils.model import MODEL_FEATURES, predict_demand

        values = {
            "previous_day_demand": 22,
            "previous_week_demand": 20,
            "rolling_7_day_avg": 21,
            "day_of_week": 4,
        }
        self.assertEqual(tuple(values), MODEL_FEATURES)
        prediction, error = predict_demand(values)
        self.assertIsNone(error)
        self.assertGreaterEqual(prediction, 0)


if __name__ == "__main__":
    unittest.main()
