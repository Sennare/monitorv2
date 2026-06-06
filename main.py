from __future__ import annotations

import asyncio
import signal
from datetime import datetime
from typing import Optional

from core.logic import (
    scroll_menu,
    update_temperature,
    update_humidity,
    set_idle_state,
)
from core.state import AppState
from displays.view import render_menu, render_screensaver
from displays.debug import DebugDisplay
from displays.oled import MockOLEDDisplay
from hardware.hal import rotary_encoder, temperature_sensor, humidity_sensor
from storage.db import MockDatabaseClient, DatabaseClient
from storage.weather import WeatherMeasurement, MockWeatherRepository


class Application:
    def __init__(self):
        self.state = AppState()
        self.db_client: DatabaseClient = MockDatabaseClient()
        self.weather_repo = MockWeatherRepository()
        self.running = True
        self.last_temp: float = 22.0
        self.last_humidity: float = 50.0
        
        # Initialize display devices
        self.debug_display = DebugDisplay()
        self.oled_display = MockOLEDDisplay()
        self.displays = [self.debug_display, self.oled_display]

    async def sensor_reader(self) -> None:
        """Read temperature and humidity every 30 seconds."""
        print("[app] Sensor reader started")
        temp_iter = temperature_sensor()
        humidity_iter = humidity_sensor()
        
        # Initial reads to prime the generators
        await temp_iter.__anext__()
        await humidity_iter.__anext__()
        
        while self.running:
            try:
                # Read temperature and humidity
                temperature = await asyncio.wait_for(
                    temp_iter.__anext__(), timeout=3.0
                )
                humidity = await asyncio.wait_for(
                    humidity_iter.__anext__(), timeout=3.0
                )
                
                # Update state
                update_temperature(self.state, temperature)
                update_humidity(self.state, humidity)
                self.last_temp = temperature
                self.last_humidity = humidity
                
                print(f"[sensor] Temp: {temperature:.1f}°C, Humidity: {humidity:.1f}%")
                
                # Wait 30 seconds before next read
                await asyncio.sleep(30)
            except asyncio.TimeoutError:
                print("[sensor] Read timeout")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"[sensor] Error: {e}")
                await asyncio.sleep(5)

    async def database_writer(self) -> None:
        """Store measurements to database every 5 minutes."""
        print("[app] Database writer started")
        await self.db_client.connect()
        
        while self.running:
            try:
                # Wait 5 minutes
                await asyncio.sleep(300)
                
                if not self.running:
                    break
                
                # Create and store measurement
                measurement = WeatherMeasurement(
                    temperature_c=self.last_temp,
                    humidity_percent=self.last_humidity,
                    timestamp=datetime.utcnow(),
                )
                await self.weather_repo.persist_measurement(measurement)
                print(f"[db] Stored measurement: {measurement}")
                
            except Exception as e:
                print(f"[db] Error: {e}")
                await asyncio.sleep(10)

    async def screensaver_loop(self) -> None:
        """Display screen saver: 10s on, 30s off, repeating."""
        print("[app] Screen saver started")
        
        # Initialize displays
        await self.debug_display.initialize()
        await self.oled_display.initialize()
        
        while self.running:
            try:
                # Display ON for 10 seconds
                await render_screensaver(
                    self.state.temperature_c,
                    self.state.humidity_percent,
                    displays=self.displays,
                )
                await asyncio.sleep(10)
                
                if not self.running:
                    break
                
                # Display OFF for 30 seconds
                print("[display] Screen OFF")
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"[screensaver] Error: {e}")
                await asyncio.sleep(5)

    async def monitor_encoder(self) -> None:
        """Monitor rotary encoder for user input."""
        print("[app] Encoder monitor started")
        async for step in rotary_encoder():
            if not self.running:
                break
            
            if step != 0:
                print(f"[encoder] User input detected: {step}")
                # User input detected - could be used to exit idle state
                # in a full implementation with a menu system

    async def shutdown(self) -> None:
        """Graceful shutdown."""
        print("[app] Shutting down...")
        self.running = False
        await self.db_client.close()
        await self.debug_display.close()
        await self.oled_display.close()
        print("[app] Shutdown complete")

    async def run(self) -> None:
        """Main application loop."""
        print("[app] Starting monitor application...")
        set_idle_state(self.state, True)
        
        # Create background tasks
        tasks = [
            asyncio.create_task(self.sensor_reader()),
            asyncio.create_task(self.database_writer()),
            asyncio.create_task(self.screensaver_loop()),
            asyncio.create_task(self.monitor_encoder()),
        ]
        
        try:
            # Run all tasks concurrently
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            print("[app] Tasks cancelled")
        except KeyboardInterrupt:
            print("[app] Keyboard interrupt")
        finally:
            await self.shutdown()
            for task in tasks:
                if not task.done():
                    task.cancel()


async def main() -> None:
    """Entry point for the application."""
    app = Application()
    
    def handle_signal(signum, frame):
        print("[main] Received signal, initiating shutdown")
        asyncio.create_task(app.shutdown())
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication stopped")
    except Exception as e:
        print(f"Fatal error: {e}")
        raise
