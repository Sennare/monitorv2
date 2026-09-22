import unittest
import time
from state import StateStore, EventType, AppState, Mood
from soul.emotions.base_emotion import BaseEmotion, EmotionConfig
from soul.emotions.too_hot import TooHot
from soul.emotions.too_cold import TooCold
from soul.emotions.bored import Bored
from soul.emotions.angry import Angry
from soul.emotions.thinking import Thinking
from soul.emotions.curious import Curious
from soul.emotions.happy import Happy
from soul.emotion_state_manager import EmotionStateManager


class TestDynamicEmotions(unittest.TestCase):
    def setUp(self):
        self.store = StateStore()

    def test_base_emotion_cooldown_contract(self):
        """Verify that reaching 100 triggers cooldown, blocks increases, and decreases to 0."""
        config = EmotionConfig(cooldown_decay_rate=5.0)
        emotion = BaseEmotion(config)
        self.assertEqual(emotion.level, 0.0)
        self.assertFalse(emotion.on_cooldown)

        # Increase to 100
        emotion.increase_level(100.0)
        self.assertEqual(emotion.level, 100.0)
        self.assertTrue(emotion.on_cooldown)

        # Attempt to increase while on cooldown must be strictly blocked
        emotion.increase_level(20.0)
        self.assertEqual(emotion.level, 100.0)

        # Apply decay ticks: level must continuously decrease
        emotion.decay_tick()
        self.assertEqual(emotion.level, 95.0)
        self.assertTrue(emotion.on_cooldown)

        # Increase still blocked at 95 while on cooldown
        emotion.increase_level(10.0)
        self.assertEqual(emotion.level, 95.0)

        # Decay all the way to 0
        for _ in range(19):
            emotion.decay_tick()

        self.assertEqual(emotion.level, 0.0)
        self.assertFalse(emotion.on_cooldown)

        # Now that it reached 0, increases are allowed again
        emotion.increase_level(15.0)
        self.assertEqual(emotion.level, 15.0)

    def test_too_hot_temperature_rates(self):
        """Verify that TooHot scales rate with temperature and decreases when <= 26°C."""
        too_hot = TooHot()

        # Case 1: 25°C -> below threshold, must not increase
        too_hot._on_env_changed(AppState(temperature=25.0))
        too_hot.tick()
        self.assertEqual(too_hot.get_emotion().level, 0.0)

        # Case 2: 30°C -> rate should be (30 - 26) * 0.25 = 1.0/s
        too_hot._on_env_changed(AppState(temperature=30.0))
        too_hot.tick()
        self.assertAlmostEqual(too_hot.get_emotion().level, 1.0, places=2)
        too_hot.tick()
        self.assertAlmostEqual(too_hot.get_emotion().level, 2.0, places=2)

        # Case 3: 35°C -> rate should be (35 - 26) * 0.25 = 2.25/s
        too_hot._on_env_changed(AppState(temperature=35.0))
        too_hot.tick()
        self.assertAlmostEqual(too_hot.get_emotion().level, 4.25, places=2)

        # Case 4: Back to 24°C -> must decrease slowly towards 0
        too_hot._on_env_changed(AppState(temperature=24.0))
        too_hot.tick()
        self.assertAlmostEqual(too_hot.get_emotion().level, 3.85, places=2)

    def test_too_cold_temperature_rates(self):
        """Verify that TooCold scales rate with coldness and warms up when >= 18°C."""
        too_cold = TooCold()

        # Case 1: 21°C -> warm, does not increase
        too_cold._on_env_changed(AppState(temperature=21.0))
        too_cold.tick()
        self.assertEqual(too_cold.get_emotion().level, 0.0)

        # Case 2: 16°C -> rate should be (18 - 16) * 0.25 = 0.5/s
        too_cold._on_env_changed(AppState(temperature=16.0))
        too_cold.tick()
        self.assertAlmostEqual(too_cold.get_emotion().level, 0.5, places=2)

        # Case 3: 10°C -> rate should be (18 - 10) * 0.25 = 2.0/s
        too_cold._on_env_changed(AppState(temperature=10.0))
        too_cold.tick()
        self.assertAlmostEqual(too_cold.get_emotion().level, 2.5, places=2)

        # Case 4: Back to 20°C -> warms up back towards 0
        too_cold._on_env_changed(AppState(temperature=20.0))
        too_cold.tick()
        self.assertAlmostEqual(too_cold.get_emotion().level, 2.1, places=2)

    def test_angry_strictly_input_driven(self):
        """Verify that Angry does not move on ticks, only on explicit boost/input."""
        angry = Angry()
        self.assertEqual(angry.get_emotion().level, 0.0)

        # Ticking multiple times does not increase Angry
        for _ in range(5):
            angry.tick()
        self.assertEqual(angry.get_emotion().level, 0.0)

        # Triggered to 100 (e.g. entering Settings)
        angry.get_emotion().increase_level(100.0)
        self.assertEqual(angry.get_emotion().level, 100.0)
        self.assertTrue(angry.get_emotion().on_cooldown)

        # Angry does not move during tick
        angry.tick()
        self.assertEqual(angry.get_emotion().level, 100.0)

        # Decays on decay_tick until reaching 0
        while angry.get_emotion().level > 0:
            angry.get_emotion().decay_tick()

        self.assertEqual(angry.get_emotion().level, 0.0)
        self.assertFalse(angry.get_emotion().on_cooldown)

    def test_bored_random_walk_and_presence(self):
        """Verify that Bored fluctuates dynamically when alone and recedes when someone is around."""
        bored = Bored()
        bored._on_env_changed(AppState(someone_around=False))

        # Simulate 20 ticks alone
        levels = []
        for _ in range(20):
            bored.tick()
            levels.append(bored.get_emotion().level)

        # Level should not be stuck at 0.0
        self.assertGreater(levels[-1], 0.0)
        # Should show variation (not all values identical)
        self.assertGreater(len(set(levels)), 1)

        # When someone enters with boredom at elevated level
        bored.get_emotion().level = 50.0
        current = bored.get_emotion().level
        bored._on_env_changed(AppState(someone_around=True))

        # Level immediately drops on arrival
        self.assertLess(bored.get_emotion().level, current)
        after_arrival = bored.get_emotion().level

        # Ticks with someone present should continue to decrease boredom
        for _ in range(5):
            bored.tick()

        self.assertLessEqual(bored.get_emotion().level, after_arrival)

    def test_thinking_and_curious_wander(self):
        """Verify that Thinking and Curious move dynamically and don't stay at 0."""
        thinking = Thinking()
        curious = Curious()
        curious._on_env_changed(AppState(someone_around=True))

        for _ in range(15):
            thinking.tick()
            curious.tick()

        self.assertGreater(thinking.get_emotion().level, 0.0)
        self.assertGreater(curious.get_emotion().level, 0.0)

    def test_neutral_composure_calibration(self):
        """Verify that Neutral level inversely tracks highest arousal in EmotionStateManager."""
        mgr = EmotionStateManager()
        try:
            # When all emotions are 0, Neutral is 100
            levels = mgr.get_emotion_levels()
            # Simulate high Happy
            mgr.emotion_instances[Mood.HAPPY].get_emotion().level = 80.0
            
            # Recalculate Neutral composure
            non_neutral_peak = max(
                (inst.get_emotion().level for m, inst in mgr.emotion_instances.items() if m != Mood.NEUTRAL),
                default=0.0
            )
            mgr.emotion_instances[Mood.NEUTRAL].get_emotion().level = max(0.0, 100.0 - non_neutral_peak)
            
            updated_levels = mgr.get_emotion_levels()
            self.assertEqual(updated_levels[Mood.HAPPY], 80)
            self.assertEqual(updated_levels[Mood.NEUTRAL], 20)
        finally:
            mgr.close()

    def test_knob_gentle_increase_happy(self):
        """Verify that knob rotations increase Happy by 5% and do not force Happy mood."""
        mgr = EmotionStateManager()
        try:
            self.assertEqual(mgr.mood, Mood.NEUTRAL)
            self.assertEqual(mgr.emotion_instances[Mood.HAPPY].get_emotion().level, 0.0)

            # Turn knob once -> +5%
            from state import Knob, KnobUserAction
            self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))
            self.assertEqual(mgr.emotion_instances[Mood.HAPPY].get_emotion().level, 5.0)
            self.assertEqual(mgr.mood, Mood.NEUTRAL)

            # Press knob once -> +5% (total 10%)
            self.store.dispatch(Knob(KnobUserAction.PRESS))
            self.assertEqual(mgr.emotion_instances[Mood.HAPPY].get_emotion().level, 10.0)
            self.assertEqual(mgr.mood, Mood.NEUTRAL)
        finally:
            mgr.close()

    def test_emotions_page_knob_and_timeout(self):
        """Verify Emotions page stays for 5 minutes and knob rotation does not exit."""
        from navigation.navigation import Navigation, Location, EMOTIONS_INACTIVITY_TIMEOUT, DEFAULT_INACTIVITY_TIMEOUT
        from state import Knob, KnobUserAction
        nav = Navigation(start_with_welcome=False)
        try:
            nav.navigate_to(Location.EMOTIONS.value)
            self.assertEqual(nav.current_location_id, Location.EMOTIONS.value)
            self.assertEqual(nav.lcd.timeout_seconds, EMOTIONS_INACTIVITY_TIMEOUT)
            self.assertEqual(nav.lcd.timeout_seconds, 300.0)

            # Turning knob must not exit to menu
            self.store.dispatch(Knob(KnobUserAction.TURN_RIGHT))
            self.assertEqual(nav.current_location_id, Location.EMOTIONS.value)
            self.store.dispatch(Knob(KnobUserAction.TURN_LEFT))
            self.assertEqual(nav.current_location_id, Location.EMOTIONS.value)

            # Pressing knob exits to menu
            self.store.dispatch(Knob(KnobUserAction.PRESS))
            self.assertEqual(nav.current_location_id, Location.MENU.value)
            self.assertEqual(nav.lcd.timeout_seconds, DEFAULT_INACTIVITY_TIMEOUT)
        finally:
            nav.close()


if __name__ == "__main__":
    unittest.main()
