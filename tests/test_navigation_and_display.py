import unittest
import time
from datetime import datetime, timedelta

from state import StateStore, EventType, Mood, AppState, Knob, KnobUserAction, BoostEmotion
from display.lcd_core import LCDCore
from display.animations.welcome import CuteCiaoAnimation
from soul.emotion_state_manager import EmotionStateManager
from navigation.navigation import Navigation, Location
from navigation.locations.menu import Menu
from navigation.locations.home import Home, bin_and_average_slots
from navigation.locations.settings import Settings


class TestLCDCoreAndNavigation(unittest.TestCase):
    def setUp(self):
        # Reset StateStore singleton state between tests
        self.store = StateStore()
        self.store.bus._listeners.clear()
        self.store._state = AppState()
        self.lcd = LCDCore(timeout_seconds=2.0)
        self.navs = []

    def tearDown(self):
        for nav in self.navs:
            nav.close()
        self.lcd.stop_animation()
        self.store.bus._listeners.clear()

    def test_lcd_concurrency_stop_animation(self):
        """Verify that starting an animation and interrupting it stops the first thread cleanly."""
        anim1 = CuteCiaoAnimation()
        anim2 = CuteCiaoAnimation()

        # Start first animation
        self.lcd.play_animation(anim1, frame_delay=0.1, cycles=10)
        self.assertTrue(self.lcd.is_screen_on)
        t1 = self.lcd._anim_thread
        self.assertIsNotNone(t1)
        self.assertTrue(t1.is_alive())

        # Start second animation immediately
        self.lcd.play_animation(anim2, frame_delay=0.1, cycles=10)
        t2 = self.lcd._anim_thread
        self.assertIsNotNone(t2)
        self.assertNotEqual(t1, t2)

        # Thread 1 should have stopped
        time.sleep(0.15)
        self.assertFalse(t1.is_alive())

        # Clean up
        self.lcd.stop_animation()
        self.assertFalse(t2.is_alive())

    def test_inactivity_timer_sleep_and_wake(self):
        """Verify display turns off after inactivity and wakes up upon knob interaction."""
        self.lcd.turn_on()
        self.assertTrue(self.lcd.is_screen_on)

        # Manually invoke turn_off
        self.lcd.turn_off()
        self.assertFalse(self.lcd.is_screen_on)

        # Navigation waking display
        nav = Navigation(start_with_welcome=False)
        self.navs.append(nav)
        self.assertEqual(nav.current_location_id, Location.HOME.value)

        # Put display to sleep
        nav.lcd.turn_off()
        self.assertFalse(nav.lcd.is_screen_on)

        # First knob interaction in the dark should wake the display without changing page
        self.store.dispatch(Knob(KnobUserAction.PRESS))
        self.assertTrue(nav.lcd.is_screen_on)
        self.assertEqual(nav.current_location_id, Location.HOME.value)

    def test_navigation_menu_and_flow(self):
        """Verify Home -> Menu -> Settings -> Menu navigation flow."""
        nav = Navigation(start_with_welcome=False)
        self.navs.append(nav)
        self.assertEqual(nav.current_location_id, Location.HOME.value)

        # Display is awake, pressing knob navigates from HOME to MENU
        nav.lcd.turn_on()
        self.store.dispatch(Knob(KnobUserAction.PRESS))
        self.assertEqual(nav.current_location_id, Location.MENU.value)

        # In menu, rotate to Settings (index 2: Home=0, Sensors=1, Settings=2)
        menu_page: Menu = nav.pages[Location.MENU.value]
        menu_page.selected_index = 0
        self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))  # index 1: Sensors
        self.assertEqual(menu_page.selected_index, 1)
        self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))  # index 2: Settings
        self.assertEqual(menu_page.selected_index, 2)

        # Press knob to enter Settings
        self.store.dispatch(Knob(KnobUserAction.PRESS))
        self.assertEqual(nav.current_location_id, Location.SETTINGS.value)

    def test_settings_triggers_angry_emotion(self):
        """Verify that entering Settings immediately triggers the ANGRY emotion in soul."""
        emotion_manager = EmotionStateManager()
        nav = Navigation(start_with_welcome=False)
        self.navs.append(nav)

        # Initially mood is Neutral
        self.assertEqual(self.store.state.mood, Mood.NEUTRAL)

        # Navigate to Settings
        nav.navigate_to(Location.SETTINGS.value)

        # Verify Angry emotion level boosted and active mood changed to ANGRY
        angry_level = emotion_manager.emotion_instances[Mood.ANGRY].get_emotion().level
        self.assertGreaterEqual(angry_level, 50)
        self.assertEqual(self.store.state.mood, Mood.ANGRY)

    def test_sensors_page_triggers_curious_emotion(self):
        """Verify that entering Sensors triggers the CURIOUS emotion in soul."""
        emotion_manager = EmotionStateManager()
        nav = Navigation(start_with_welcome=False)
        self.navs.append(nav)

        nav.navigate_to(Location.SENSORS.value)
        curious_level = emotion_manager.emotion_instances[Mood.CURIOUS].get_emotion().level
        self.assertGreaterEqual(curious_level, 50)
        self.assertEqual(self.store.state.mood, Mood.CURIOUS)

    def test_welcome_page_skip_on_knob(self):
        """Verify that interacting during Welcome skips directly to Home."""
        nav = Navigation(start_with_welcome=True)
        self.navs.append(nav)
        self.assertEqual(nav.current_location_id, Location.WELCOME.value)

        # User turns knob
        self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))
        self.assertEqual(nav.current_location_id, Location.HOME.value)

    def test_home_knob_time_travel_and_menu_press(self):
        """Verify Home rotary scrolling shifts hours back, caps forward at 0, and PRESS navigates to Menu."""
        nav = Navigation(start_with_welcome=False)
        self.navs.append(nav)
        home_page: Home = nav.pages[Location.HOME.value]
        self.assertEqual(home_page.hours_offset, 0)

        # Rotate left: go back in time
        self.store.dispatch(Knob(KnobUserAction.TURN_LEFT))
        self.assertEqual(home_page.hours_offset, 1)
        self.assertEqual(nav.current_location_id, Location.HOME.value)

        self.store.dispatch(Knob(KnobUserAction.TURN_LEFT))
        self.assertEqual(home_page.hours_offset, 2)

        # Rotate right: scroll forward towards now
        self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))
        self.assertEqual(home_page.hours_offset, 1)

        self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))
        self.assertEqual(home_page.hours_offset, 0)

        # Rotate right again: MUST NOT go into future (stop at 0)
        self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))
        self.assertEqual(home_page.hours_offset, 0)

        # Pressing knob on Home navigates to Menu
        self.store.dispatch(Knob(KnobUserAction.PRESS))
        self.assertEqual(nav.current_location_id, Location.MENU.value)

    def test_home_reset_time_travel_on_reenter_and_wake(self):
        """Verify time travel resets to 0 when re-entering Home or waking up from sleep."""
        nav = Navigation(start_with_welcome=False)
        self.navs.append(nav)
        home_page: Home = nav.pages[Location.HOME.value]

        # Shift time back
        home_page.hours_offset = 8

        # Navigate away to Menu and back to Home
        nav.navigate_to(Location.MENU.value)
        self.assertEqual(nav.current_location_id, Location.MENU.value)

        nav.navigate_to(Location.HOME.value)
        self.assertEqual(nav.current_location_id, Location.HOME.value)
        self.assertEqual(home_page.hours_offset, 0, "Entering Home should reset time travel to 0")

        # Shift time back again
        home_page.hours_offset = 12

        # Display goes to sleep
        nav.lcd.turn_off()
        self.assertFalse(nav.lcd.is_screen_on)

        # Interaction in sleep wakes display and resets Home to 0
        self.store.dispatch(Knob(KnobUserAction.TURN_LEFT))
        self.assertTrue(nav.lcd.is_screen_on)
        self.assertEqual(home_page.hours_offset, 0, "Waking display should reset time travel to 0")

    def test_bin_and_average_slots(self):
        """Verify time-series telemetry is correctly slotted per pixel width, averaged, and interpolated."""
        now = datetime(2026, 9, 22, 12, 0, 0)
        start_time = now - timedelta(hours=24)
        width_px = 24  # 1 pixel per hour for clean assertions

        # Generate sample points:
        # Hour 0: two readings (20.0 and 22.0 -> avg 21.0, humi 50 and 60 -> avg 55.0)
        # Hour 2: one reading (25.0, 70.0)
        # Hour 1 has no readings -> should be interpolated between Hour 0 and Hour 2!
        raw_data = [
            (start_time + timedelta(minutes=10), 20.0, 50.0),
            (start_time + timedelta(minutes=40), 22.0, 60.0),
            (start_time + timedelta(hours=2, minutes=30), 26.0, 70.0),
        ]

        temp_series, humi_series = bin_and_average_slots(raw_data, start_time, now, width_px)

        self.assertEqual(len(temp_series), width_px)
        self.assertEqual(len(humi_series), width_px)

        # Hour 0 average
        self.assertAlmostEqual(temp_series[0], 21.0, places=2)
        self.assertAlmostEqual(humi_series[0], 55.0, places=2)

        # Hour 2 average
        self.assertAlmostEqual(temp_series[2], 26.0, places=2)
        self.assertAlmostEqual(humi_series[2], 70.0, places=2)

        # Hour 1 interpolated (midpoint between 21.0 and 26.0 -> 23.5)
        self.assertAlmostEqual(temp_series[1], 23.5, places=2)
        self.assertAlmostEqual(humi_series[1], 62.5, places=2)

    def test_home_render_with_and_without_data(self):
        """Verify Home.render() executes without error both when telemetry is available and when empty."""
        class MockDB:
            def fetch_time_range(self, start_time, end_time):
                return [
                    (start_time + timedelta(hours=1), 22.5, 45.0),
                    (start_time + timedelta(hours=5), 23.1, 48.0),
                    (start_time + timedelta(hours=18), 21.0, 52.0),
                ]

        home_with_data = Home(db=MockDB())
        state = AppState(temperature=22.4, humidity=50.0)
        # Should render without exception
        home_with_data.render(self.lcd, state)

        # Render with time travel offset
        home_with_data.hours_offset = 3
        home_with_data.render(self.lcd, state)

        # Empty DB
        class EmptyDB:
            def fetch_time_range(self, start_time, end_time):
                return []

        home_empty = Home(db=EmptyDB())
        home_empty.render(self.lcd, state)


if __name__ == "__main__":
    unittest.main()
