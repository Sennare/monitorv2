from state import StateStore, SetTemAndHumi, TempAndHumi
import threading
import time

try:
    import board
    import busio
    import adafruit_ahtx0
    HARDWARE_AVAILABLE = True
except (ImportError, NotImplementedError):
    board = None
    busio = None
    adafruit_ahtx0 = None
    HARDWARE_AVAILABLE = False


class Temp:
    def __init__(self):
        self.debug = False
        self.sensor = None
        if HARDWARE_AVAILABLE and board is not None and busio is not None and adafruit_ahtx0 is not None:
            try:
                i2c_bus = busio.I2C(board.SCL, board.SDA)
                self.sensor = adafruit_ahtx0.AHTx0(i2c_bus)
            except Exception as e:
                print(f"[Temp] Hardware init failed ({e}), sensor unavailable")
        self.state_store = StateStore()
        self._stop_event = threading.Event()
        self._is_closed = False
        self._backlight_watchdog_thread = threading.Thread(target=self._measure_loop, daemon=True)
        self._backlight_watchdog_thread.start()
    
    def _measure_loop(self):
        while not self._stop_event.is_set():
            if self._stop_event.wait(timeout=5):
                break
            if self.sensor is None:
                continue
            try:
                sensor = self.sensor
                if self.debug:
                    print(f"[Temp] mesuring temp {sensor.temperature}")
                    print(f"[Temp] mesuring humi {sensor.relative_humidity}")
                temp_and_humi = TempAndHumi(sensor.temperature, sensor.relative_humidity)
                self.state_store.dispatch(SetTemAndHumi(temp_and_humi))
            except Exception as e:
                if not self._stop_event.is_set():
                    print(f"[Temp] Error reading sensor: {e}")

    def close(self) -> None:
        """Stops the measurement thread cleanly."""
        if self._is_closed:
            return
        self._is_closed = True
        self._stop_event.set()
        if (
            hasattr(self, "_backlight_watchdog_thread")
            and self._backlight_watchdog_thread.is_alive()
            and threading.current_thread() != self._backlight_watchdog_thread
        ):
            self._backlight_watchdog_thread.join(timeout=1.0)

