from luma.core.interface.serial import i2c
from luma.core.interface.parallel import bitbang_6800
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
from state import EventType, Mood, SetMood, StateStore
import threading
import time
from soul.moods import load_frames

class OledDisplay:
    def __init__(self):
        serial = i2c(port=1, address=0x3C)
        self.device = ssd1306(serial, width=128, height=64, rotate=0)
        self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)

        self.state_store = StateStore()
        self.state_store.subscribe(EventType.MOOD_CHANGED.value, self._on_mood_changed)

        # Animation control
        self.current_mood = Mood.NEUTRAL
        self._anim_thread: threading.Thread | None = None
        self._anim_stop = threading.Event()
        # start initial animation
        self._start_animation(self.current_mood)

    def _on_mood_changed(self, mood: Mood) -> None:
        # Start animating frames for the provided mood
        print(f"[oled] Mood changed to {mood.value}, updating display...")
        # update current mood and restart animation thread
        self.current_mood = mood
        self._restart_animation()

    def _start_animation(self, mood: Mood) -> None:
        """Start animation thread for given mood."""
        # ensure any previous thread is stopped
        self._anim_stop.clear()
        def runner():
            try:
                frames = load_frames(mood.value)
            except Exception:
                frames = [Image.new("1", (128, 64))]
            idx = 0
            while not self._anim_stop.is_set() and self.current_mood == mood:
                frame = frames[idx % len(frames)]
                try:
                    self.device.display(frame)
                except Exception:
                    print("[oled] Error displaying frame, skipping...")
                    pass
                idx += 1
                # 500ms per frame
                time.sleep(0.5)

        t = threading.Thread(target=runner, daemon=True)
        self._anim_thread = t
        t.start()

    def _restart_animation(self) -> None:
        # stop existing animation
        if self._anim_thread and self._anim_thread.is_alive():
            self._anim_stop.set()
            # allow thread to exit
            self._anim_thread.join(timeout=0.6)
        # clear stop flag and start new animation
        self._anim_stop.clear()
        self._start_animation(self.current_mood)

    def display_message(self, message: str) -> None:
        # Kept fallback method just in case you need text elsewhere
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), message, fill="white", font=self.font)
        self.device.display(image)