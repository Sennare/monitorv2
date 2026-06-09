from state import StateStore, SetTemAndHumi, TempAndHumi
import threading
import time
import board
import busio
import adafruit_ahtx0 

class Temp:
    def __init__(self):
        i2c_bus = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_ahtx0.AHTx0(i2c_bus)
        self.state_store = StateStore()
        self._backlight_watchdog_thread = threading.Thread(target=self._measure_loop, daemon=True)
        self._backlight_watchdog_thread.start()
    
    def _measure_loop(self):
        while True:
            time.sleep(5)
            sensor = self.sensor
            print(f"[Temp] mesuring temp {sensor.temperature}");
            print(f"[Temp] mesuring humi {sensor.relative_humidity}");
            temp_and_humi = TempAndHumi(sensor.temperature, sensor.relative_humidity)
            self.state_store.dispatch(SetTemAndHumi(temp_and_humi))

