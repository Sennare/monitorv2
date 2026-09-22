import asyncio
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

from display.oled import OledDisplay
from display.lcd_core import LCDCore
from input.temp import Temp
from database.librian import Librian
from input.movement import Movement
from input.knob_controller2 import KnobController
from soul.emotion_state_manager import EmotionStateManager
from state import StateStore, AppState
import main


class TestGracefulShutdown(unittest.TestCase):
    def setUp(self):
        # Reset StateStore singleton before each test
        store = StateStore()
        store.bus._listeners.clear()
        store._state = AppState()

    def tearDown(self):
        store = StateStore()
        store.bus._listeners.clear()

    def test_oled_display_close_stops_thread(self):
        disp = OledDisplay()
        self.assertTrue(disp._anim_thread.is_alive())

        disp.close()
        # Thread should stop and join within timeout
        self.assertFalse(disp._anim_thread.is_alive())

        # Calling close again should be idempotent
        disp.close()
        self.assertTrue(disp._is_closed)

    def test_temp_close_stops_thread(self):
        temp = Temp()
        self.assertTrue(temp._backlight_watchdog_thread.is_alive())

        temp.close()
        self.assertFalse(temp._backlight_watchdog_thread.is_alive())

    def test_librian_close_stops_thread(self):
        with patch("database.librian.Database"):
            librian = Librian()
            self.assertTrue(librian._persist_thread.is_alive())

            librian.close()
            self.assertFalse(librian._persist_thread.is_alive())

    def test_movement_close_cleans_timer(self):
        movement = Movement()
        # Trigger movement to arm timer
        movement._movement_detected()
        self.assertIsNotNone(movement._no_movement_timer)

        movement.close()
        self.assertIsNone(movement._no_movement_timer)

    def test_application_close_terminates_all_daemon_threads(self):
        with patch("database.librian.Database"):
            app = main.Application()

            # Verify threads are active
            self.assertTrue(app.oled_display._anim_thread.is_alive())
            self.assertTrue(app.navigation._auto_refresh_thread.is_alive())
            self.assertTrue(app.temp._backlight_watchdog_thread.is_alive())
            self.assertTrue(app.librian._persist_thread.is_alive())

            app.close()

            # Verify all threads stopped cleanly
            self.assertFalse(app.oled_display._anim_thread.is_alive())
            self.assertFalse(app.navigation._auto_refresh_thread.is_alive())
            self.assertFalse(app.temp._backlight_watchdog_thread.is_alive())
            self.assertFalse(app.librian._persist_thread.is_alive())
            self.assertTrue(app._is_closed)

    def test_application_run_handles_cancellation(self):
        async def run_and_cancel():
            with patch("database.librian.Database"):
                app = main.Application()
                try:
                    task = asyncio.create_task(app.run())
                    # Yield to loop to let task run
                    await asyncio.sleep(0.05)
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                finally:
                    app.close()

                self.assertFalse(app.oled_display._anim_thread.is_alive())
                self.assertFalse(app.navigation._auto_refresh_thread.is_alive())

        asyncio.run(run_and_cancel())


if __name__ == "__main__":
    unittest.main()
