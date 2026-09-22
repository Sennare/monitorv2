import unittest
import time
from datetime import datetime, timedelta

from state import StateStore, EventType, Mood, AppState, Knob, KnobUserAction, BoostEmotion, SetTemAndHumi, TempAndHumi, SetEmotionLevels
from display.lcd_core import LCDCore
from display.animations.welcome import CuteCiaoAnimation
from soul.emotion_state_manager import EmotionStateManager
from navigation.navigation import Navigation, Location
from navigation.locations.menu import Menu
from navigation.locations.home import Home, get_temp_color
from navigation.locations.settings import Settings
from navigation.locations.emotions_page import EmotionsPage


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

        # In menu, rotate to Settings (index 3: Home=0, Sensors=1, Emotions=2, Settings=3)
        menu_page: Menu = nav.pages[Location.MENU.value]
        menu_page.selected_index = 0
        self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))  # index 1: Sensors
        self.assertEqual(menu_page.selected_index, 1)
        self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))  # index 2: Emotions
        self.assertEqual(menu_page.selected_index, 2)
        self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))  # index 3: Settings
        self.assertEqual(menu_page.selected_index, 3)

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

    def test_home_knob_and_menu_press(self):
        """Verify Home PRESS navigates to Menu and rotation has no scroll effect."""
        nav = Navigation(start_with_welcome=False)
        self.navs.append(nav)

        # Rotate left: no scroll, stays on HOME
        self.store.dispatch(Knob(KnobUserAction.TURN_LEFT))
        self.assertEqual(nav.current_location_id, Location.HOME.value)

        # Rotate right: no scroll, stays on HOME
        self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))
        self.assertEqual(nav.current_location_id, Location.HOME.value)

        # Pressing knob on Home navigates to Menu
        self.store.dispatch(Knob(KnobUserAction.PRESS))
        self.assertEqual(nav.current_location_id, Location.MENU.value)

    def test_home_render_tracks_temperature_and_humidity(self):
        """Verify Home.render() tracks latest telemetry and mood without error."""
        home = Home()
        state = AppState(temperature=22.4, humidity=50.0, mood=Mood.HAPPY)
        home.render(self.lcd, state)
        self.assertEqual(home.temperature, 22.4)
        self.assertEqual(home.humidity, 50.0)
        self.assertEqual(home.mood, Mood.HAPPY)

        # Default state
        home_empty = Home()
        home_empty.render(self.lcd, AppState())
        self.assertEqual(home_empty.temperature, 0)
        self.assertEqual(home_empty.humidity, 0)
        self.assertEqual(home_empty.mood, Mood.NEUTRAL)

        # Cold rendering with different moods
        home.render(self.lcd, AppState(temperature=8.0, humidity=40.0, mood=Mood.TOO_COLD))
        self.assertEqual(home.mood, Mood.TOO_COLD)

        # Hot rendering
        home.render(self.lcd, AppState(temperature=35.0, humidity=80.0, mood=Mood.TOO_HOT))
        self.assertEqual(home.mood, Mood.TOO_HOT)

    def test_get_temp_color(self):
        """Verify temperature color changes from blue (cold) to green/yellow (mild) to red (hot)."""
        cold_color = get_temp_color(5.0)
        self.assertEqual(cold_color, (59, 130, 246))  # Cold blue

        mild_color = get_temp_color(20.0)
        self.assertEqual(mild_color, (34, 197, 94))  # Green

        hot_color = get_temp_color(36.0)
        self.assertEqual(hot_color, (239, 68, 68))  # Hot red

        # Verify red component increases with temperature
        self.assertLess(cold_color[0], hot_color[0])
        # Verify blue component decreases with temperature
        self.assertGreater(cold_color[2], hot_color[2])

    def test_inactivity_timeout_falls_back_to_home_and_shuts_down_backlight(self):
        """Verify 45s inactivity from another page falls back to Home and turns off backlight."""
        nav = Navigation(start_with_welcome=False)
        self.navs.append(nav)

        # User is in Settings
        nav.navigate_to(Location.SETTINGS.value)
        self.assertEqual(nav.current_location_id, Location.SETTINGS.value)
        self.assertTrue(nav.lcd.is_screen_on)

        # 45s inactivity triggers
        nav._on_inactivity_timeout()

        # Should fall back to Home and turn off backlight
        self.assertEqual(nav.current_location_id, Location.HOME.value)
        self.assertFalse(nav.lcd.is_screen_on, "Backlight should be turned off")

    def test_inactivity_timeout_on_home_shuts_down_backlight(self):
        """Verify 45s inactivity on Home turns off backlight."""
        nav = Navigation(start_with_welcome=False)
        self.navs.append(nav)
        self.assertTrue(nav.lcd.is_screen_on)

        # 45s inactivity triggers
        nav._on_inactivity_timeout()

        # Backlight turned off
        self.assertFalse(nav.lcd.is_screen_on, "Backlight should be turned off")

    def test_telemetry_update_does_not_wake_display_or_reset_inactivity_timer(self):
        """Verify background sensor events do not inadvertently wake display or reset inactivity timer."""
        nav = Navigation(start_with_welcome=False)
        self.navs.append(nav)

        # Display sleeps
        nav.lcd.turn_off()
        self.assertFalse(nav.lcd.is_screen_on)

        # Sensor dispatches telemetry update
        self.store.dispatch(SetTemAndHumi(TempAndHumi(24.5, 55.0)))

        # Display should stay off (no waking from background sensor loops)
        self.assertFalse(nav.lcd.is_screen_on)

    def test_turn_off_shuts_down_backlight_without_blanking_lcd_image(self):
        """Verify turn_off only disables the backlight pin and preserves LCD pixel buffer content."""
        # Paint red on the display image
        self.lcd.turn_on()
        self.lcd.draw.rectangle((0, 0, 50, 50), fill=(255, 0, 0))

        # Turn off backlight
        self.lcd.turn_off()
        self.assertFalse(self.lcd.is_screen_on)

        # Check that the image was not overwritten by a black rectangle
        pixel = self.lcd.image.getpixel((25, 25))
        self.assertEqual(pixel, (255, 0, 0), "LCD image buffer should be preserved when backlight turns off")

    def test_lcd_brightness_control(self):
        """Verify LCDCore set_brightness clamps between 10% and 100% and preserves state across sleep."""
        self.lcd.set_brightness(70)
        self.assertEqual(self.lcd.get_brightness(), 70)

        # Clamping
        self.lcd.set_brightness(150)
        self.assertEqual(self.lcd.get_brightness(), 100)
        self.lcd.set_brightness(0)
        self.assertEqual(self.lcd.get_brightness(), 10)

        # Preserved across sleep/wake
        self.lcd.set_brightness(80)
        self.lcd.turn_off()
        self.assertEqual(self.lcd.get_brightness(), 80)
        self.lcd.turn_on()
        self.assertEqual(self.lcd.get_brightness(), 80)

    def test_settings_adjust_brightness_with_knob(self):
        """Verify user can select and adjust backlight brightness via rotary knob in Settings."""
        nav = Navigation(start_with_welcome=False)
        self.navs.append(nav)

        nav.navigate_to(Location.SETTINGS.value)
        settings_page: Settings = nav.pages[Location.SETTINGS.value]
        self.lcd.set_brightness(50)

        # Select Backlight Brightness item (index 1)
        settings_page.selected_index = 1
        self.assertFalse(settings_page.is_editing_brightness)

        # Press knob to enter editing mode
        self.store.dispatch(Knob(KnobUserAction.PRESS))
        self.assertTrue(settings_page.is_editing_brightness)

        # Turn right to increase brightness (+10% -> 60%)
        self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))
        self.assertEqual(self.lcd.get_brightness(), 60)

        self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))
        self.assertEqual(self.lcd.get_brightness(), 70)

        # Turn left to decrease brightness (-10% -> 60%)
        self.store.dispatch(Knob(KnobUserAction.TURN_LEFT))
        self.assertEqual(self.lcd.get_brightness(), 60)

        # Press to save / exit editing mode
        self.store.dispatch(Knob(KnobUserAction.PRESS))
        self.assertFalse(settings_page.is_editing_brightness)
        self.assertEqual(self.lcd.get_brightness(), 60)

    def test_lcd_pwm_frequency(self):
        """Verify LCDCore exposes pwm_freq and defaults to 1000 Hz."""
        self.assertTrue(hasattr(self.lcd, "pwm_freq"))
        self.assertGreaterEqual(self.lcd.pwm_freq, 1000)

    def test_lcd_sleep_dimming_to_5_percent(self):
        """Verify LCDCore dims backlight to 5% instead of 0% when screen is asleep."""
        self.assertEqual(self.lcd.sleep_brightness, 5)
        self.lcd.set_brightness(75)
        self.lcd.turn_on()
        self.assertEqual(self.lcd.get_effective_brightness(), 75)
        self.lcd.turn_off()
        self.assertFalse(self.lcd.is_screen_on)
        self.assertEqual(self.lcd.get_effective_brightness(), 5)
        self.assertEqual(self.lcd.get_brightness(), 75, "Active brightness target preserved")

    def test_knob_rotation_triggers_happy_emotion(self):
        """Verify rotating knob gently increases Happy (+5%) without forcing happy face until reaching 50."""
        emotion_manager = EmotionStateManager()
        self.assertEqual(self.store.state.mood, Mood.NEUTRAL)

        # Single rotation: increases Happy by 5.0%, mood remains Neutral (threshold 50 not met)
        self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))
        self.assertEqual(emotion_manager.emotion_instances[Mood.HAPPY].get_emotion().level, 5.0)
        self.assertEqual(self.store.state.mood, Mood.NEUTRAL)

        # Multiple rotations: accumulates to 50% and activates Happy mood naturally
        for _ in range(9):
            self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))

        self.assertEqual(self.store.state.mood, Mood.HAPPY)
        self.assertGreaterEqual(emotion_manager.emotion_instances[Mood.HAPPY].get_emotion().level, 50)
        emotion_manager.close()

    def test_knob_then_settings_triggers_angry_emotion(self):
        """Verify navigating to Settings after turning knob properly switches mood from Happy to Angry."""
        emotion_manager = EmotionStateManager()
        nav = Navigation(start_with_welcome=False)
        self.navs.append(nav)

        # Rotate knob 10 times -> triggers Happy naturally
        for _ in range(10):
            self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))
        self.assertEqual(self.store.state.mood, Mood.HAPPY)

        # Navigate to Settings -> must trigger Angry, overriding Happy
        nav.navigate_to(Location.SETTINGS.value)
        self.assertEqual(self.store.state.mood, Mood.ANGRY)
        self.assertGreaterEqual(emotion_manager.emotion_instances[Mood.ANGRY].get_emotion().level, 50)

        # Rotating knob while in Settings should not revert mood to Happy
        self.store.dispatch(Knob(KnobUserAction.TURN_LEFT))
        self.assertEqual(self.store.state.mood, Mood.ANGRY)
        emotion_manager.close()

    def test_navigation_menu_and_emotions_flow(self):
        """Verify Home -> Menu -> Emotions (5m timeout, knob rotate stays, press exits) -> Menu flow."""
        nav = Navigation(start_with_welcome=False)
        self.navs.append(nav)
        self.assertEqual(nav.current_location_id, Location.HOME.value)
        self.assertEqual(nav.lcd.timeout_seconds, 45.0)

        # Press knob to enter Menu
        self.store.dispatch(Knob(KnobUserAction.PRESS))
        self.assertEqual(nav.current_location_id, Location.MENU.value)

        # Rotate to Emotions (index 2)
        menu_page: Menu = nav.pages[Location.MENU.value]
        menu_page.selected_index = 0
        self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))  # 1: Sensors
        self.assertEqual(menu_page.selected_index, 1)
        self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))  # 2: Emotions
        self.assertEqual(menu_page.selected_index, 2)

        # Press knob to enter Emotions view
        self.store.dispatch(Knob(KnobUserAction.PRESS))
        self.assertEqual(nav.current_location_id, Location.EMOTIONS.value)
        # Inactivity timeout must be 5 minutes (300 seconds) on EmotionsPage
        self.assertEqual(nav.lcd.timeout_seconds, 300.0)

        # Rotating knob inside Emotions must NOT exit to Menu
        self.store.dispatch(Knob(KnobUserAction.TURN_LEFT))
        self.assertEqual(nav.current_location_id, Location.EMOTIONS.value)
        self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))
        self.assertEqual(nav.current_location_id, Location.EMOTIONS.value)

        # Only pressing knob inside Emotions returns back to Menu
        self.store.dispatch(Knob(KnobUserAction.PRESS))
        self.assertEqual(nav.current_location_id, Location.MENU.value)
        self.assertEqual(nav.lcd.timeout_seconds, 45.0)

    def test_emotions_page_render_all_bars_and_active_highlight(self):
        """Verify EmotionsPage renders all 11 emotions with bars and active highlight without crashing."""
        emotions_page = EmotionsPage()
        levels = {
            Mood.HAPPY: 80,
            Mood.CURIOUS: 45,
            Mood.THINKING: 10,
            Mood.LOOKING_AROUND: 90,
            Mood.NEUTRAL: 0,
            Mood.BORED: 25,
            Mood.CONFUSED: 15,
            Mood.SAD: 30,
            Mood.ANGRY: 70,
            Mood.TOO_COLD: 5,
            Mood.TOO_HOT: 0,
        }
        state = AppState(mood=Mood.HAPPY, emotion_levels=levels)
        emotions_page.render(self.lcd, state)

        # Render with different active mood and check stability
        for test_mood in (Mood.ANGRY, Mood.NEUTRAL, Mood.CURIOUS, Mood.LOOKING_AROUND):
            st = AppState(mood=test_mood, emotion_levels=levels)
            emotions_page.render(self.lcd, st)

    def test_set_emotion_levels_action_and_event(self):
        """Verify SetEmotionLevels updates AppState and dispatches EventType.EMOTIONS_UPDATED."""
        received = []
        unsub = self.store.subscribe(EventType.EMOTIONS_UPDATED.value, lambda payload: received.append(payload))

        new_levels = {Mood.HAPPY: 95, Mood.ANGRY: 40}
        self.store.dispatch(SetEmotionLevels(new_levels))

        self.assertEqual(self.store.state.emotion_levels[Mood.HAPPY], 95)
        self.assertEqual(self.store.state.emotion_levels[Mood.ANGRY], 40)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][Mood.HAPPY], 95)
        unsub()

    def test_emotions_view_refreshes_on_emotions_updated(self):
        """Verify Navigation re-renders when on EMOTIONS page upon receiving EMOTIONS_UPDATED."""
        nav = Navigation(start_with_welcome=False)
        self.navs.append(nav)

        nav.navigate_to(Location.EMOTIONS.value)
        self.assertEqual(nav.current_location_id, Location.EMOTIONS.value)

        # Dispatch emotion level update
        render_called = False
        orig_render = nav.render
        def mock_render():
            nonlocal render_called
            render_called = True
            orig_render()
        nav.render = mock_render

        self.store.dispatch(SetEmotionLevels({Mood.HAPPY: 75}))
        self.assertTrue(render_called)


if __name__ == "__main__":
    unittest.main()
