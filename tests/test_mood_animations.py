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


if __name__ == "__main__":
    unittest.main()
