import unittest
import time
from state import StateStore, EventType, Mood, AppState, Knob, KnobUserAction, BoostEmotion
from display.lcd_core import LCDCore
from display.animations.welcome import CuteCiaoAnimation
from display.animations.cat_blink import CuteCatBlinkAnimation
from soul.emotion_state_manager import EmotionStateManager
from navigation.navigation import Navigation, Location
from navigation.locations.menu import Menu
from navigation.locations.home import Home
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
        anim2 = CuteCatBlinkAnimation()

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

    def test_cat_mascot_page_and_exit(self):
        """Verify navigating to Cat mascot page and returning to Menu."""
        nav = Navigation(start_with_welcome=False)
        self.navs.append(nav)
        nav.navigate_to(Location.CAT.value)
        self.assertEqual(nav.current_location_id, Location.CAT.value)

        # Interacting with knob exits to Menu
        self.store.dispatch(Knob(KnobUserAction.PRESS))
        self.assertEqual(nav.current_location_id, Location.MENU.value)


if __name__ == "__main__":
    unittest.main()
