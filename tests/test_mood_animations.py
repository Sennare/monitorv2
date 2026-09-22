import unittest
from PIL import Image
from state import Mood
from soul.moods import load_frames


class TestMoodAnimations(unittest.TestCase):
    def test_all_moods_load_valid_frames(self):
        """Verify all 11 moods load smoothly and produce valid monochrome 128x64 frames."""
        all_moods = list(Mood)
        self.assertEqual(len(all_moods), 11)

        for mood in all_moods:
            with self.subTest(mood=mood.value):
                frames = load_frames(mood.value)
                self.assertIsInstance(frames, list)
                self.assertGreater(len(frames), 0, f"Mood {mood.value} returned no frames")

                for idx, frame in enumerate(frames):
                    self.assertIsInstance(frame, Image.Image)
                    self.assertEqual(frame.size, (128, 64), f"Frame {idx} of {mood.value} bad size")
                    self.assertEqual(frame.mode, "1", f"Frame {idx} of {mood.value} bad mode")

                    # Verify that frame is not completely blank (has white pixels)
                    extrema = frame.getextrema()
                    self.assertEqual(
                        extrema,
                        (0, 255),
                        f"Frame {idx} of {mood.value} is completely blank"
                    )

    def test_no_mouth_rendered_in_neutral_or_idle(self):
        """Verify no mouth geometry is rendered in the traditional mouth area."""
        # Previously mouth was drawn between y=44 and y=58, centered around x=64
        neutral_frames = load_frames(Mood.NEUTRAL.value)
        for idx, frame in enumerate(neutral_frames):
            # Check center bottom area: x in [56..72], y in [48..60]
            for y in range(48, 60):
                for x in range(56, 72):
                    pixel = frame.getpixel((x, y))
                    self.assertEqual(
                        pixel,
                        0,
                        f"Found non-black pixel at ({x}, {y}) in frame {idx} of neutral (residual mouth)"
                    )

    def test_fallback_on_invalid_mood(self):
        """Verify invalid mood name falls back gracefully to neutral frames."""
        frames = load_frames("non_existent_mood_12345")
        self.assertIsInstance(frames, list)
        self.assertGreater(len(frames), 0)
        self.assertEqual(frames[0].size, (128, 64))

    def test_frame_counts_sufficient_for_high_fps(self):
        """Verify each mood produces at least 20 frames for smooth 20 FPS playback."""
        for mood in Mood:
            with self.subTest(mood=mood.value):
                frames = load_frames(mood.value)
                self.assertGreaterEqual(
                    len(frames),
                    20,
                    f"Mood {mood.value} has only {len(frames)} frames, which is too short for smooth 20 FPS"
                )

    def test_oled_display_fps_configuration(self):
        """Verify OledDisplay defaults to 20 FPS and accepts custom framerates."""
        from display.oled import OledDisplay, DEFAULT_FPS
        self.assertEqual(DEFAULT_FPS, 20.0)

        disp = OledDisplay()
        self.assertEqual(disp.fps, 20.0)
        self.assertAlmostEqual(disp.frame_delay, 0.05, places=4)

        disp_custom = OledDisplay(fps=25.0)
        self.assertEqual(disp_custom.fps, 25.0)
        self.assertAlmostEqual(disp_custom.frame_delay, 0.04, places=4)


if __name__ == "__main__":
    unittest.main()
