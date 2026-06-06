from __future__ import annotations

import asyncio
import random
from typing import AsyncIterator, Optional, Callable


class HardwareReadError(Exception):
    pass


# Try to initialize real sensor
_real_sensor_available: bool = False
_temperature_reader: Optional[Callable[[], tuple[float, float]]] = None


def _init_real_sensor() -> bool:
    """Try to initialize real DHT or BME280 sensor. Returns True if successful."""
    global _real_sensor_available, _temperature_reader
    
    try:
        # Try DHT sensor first (DHT11, DHT22, etc.)
        try:
            import adafruit_dht
            import board
            
            dht = adafruit_dht.DHT22(board.D4)  # GPIO 4 is common for DHT
            print("[hal] Real DHT22 sensor initialized on GPIO 4")
            
            def read_dht() -> tuple[float, float]:
                temp = dht.temperature
                humidity = dht.humidity
                if temp is None or humidity is None:
                    raise HardwareReadError("Failed to read DHT sensor")
                return float(temp), float(humidity)
            
            _temperature_reader = read_dht
            _real_sensor_available = True
            return True
        except (ImportError, AttributeError):
            pass
        
        # Try BME280 sensor as fallback
        try:
            import board
            import adafruit_bmp280
            
            i2c = board.I2C()
            bme280 = adafruit_bmp280.Adafruit_BME280_I2C(i2c)
            print("[hal] Real BME280 sensor initialized")
            
            def read_bme280() -> tuple[float, float]:
                temp = bme280.temperature
                humidity = bme280.humidity
                if temp is None or humidity is None:
                    raise HardwareReadError("Failed to read BME280 sensor")
                return float(temp), float(humidity)
            
            _temperature_reader = read_bme280
            _real_sensor_available = True
            return True
        except (ImportError, AttributeError):
            pass
        
        # Try generic sensor via pyA20
        try:
            from pyA20.gpio import gpio
            from pyA20.gpio import port
            
            # This is a fallback for other Allwinner boards
            print("[hal] Real sensor support for Allwinner boards (requires custom implementation)")
            _real_sensor_available = False
        except (ImportError, AttributeError):
            pass
        
    except Exception as e:
        print(f"[hal] Real sensor initialization failed: {e}")
        _real_sensor_available = False
    
    return False


# Try to initialize real sensor on module load
_init_real_sensor()


async def temperature_sensor() -> AsyncIterator[float]:
    """Read temperature from real sensor if available, otherwise use mock."""
    use_real = _real_sensor_available and _temperature_reader is not None
    
    if use_real:
        print("[hal] Using real temperature/humidity sensor")
    else:
        print("[hal] Using mock temperature/humidity sensor")
    
    while True:
        try:
            await asyncio.sleep(2.0)
            
            if use_real and _temperature_reader:
                try:
                    temperature, _ = _temperature_reader()
                except Exception as error:
                    print(f"[hal] Real sensor read failed, falling back to mock: {error}")
                    temperature = 22.0 + random.uniform(-2.0, 2.0)
            else:
                # Mock data
                temperature = 22.0 + random.uniform(-2.0, 2.0)
            
            yield temperature
        except Exception as error:
            print(f"[hal] Temperature sensor error: {error}")
            await asyncio.sleep(1.0)


async def humidity_sensor() -> AsyncIterator[float]:
    """Read humidity from real sensor if available, otherwise use mock."""
    use_real = _real_sensor_available and _temperature_reader is not None
    
    while True:
        try:
            await asyncio.sleep(2.0)
            
            if use_real and _temperature_reader:
                try:
                    _, humidity = _temperature_reader()
                except Exception as error:
                    print(f"[hal] Real sensor read failed, falling back to mock: {error}")
                    humidity = 50.0 + random.uniform(-10.0, 10.0)
            else:
                # Mock data
                humidity = 50.0 + random.uniform(-10.0, 10.0)
            
            yield max(0.0, min(100.0, humidity))
        except Exception as error:
            print(f"[hal] Humidity sensor error: {error}")
            await asyncio.sleep(1.0)


async def rotary_encoder() -> AsyncIterator[int]:
    step_options = [-1, 0, 1]
    while True:
        try:
            await asyncio.sleep(0.5)
            step = random.choice(step_options)
            yield step
        except Exception as error:
            print(f"[hal] Rotary encoder error: {error}")
            await asyncio.sleep(0.5)
