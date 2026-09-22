from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
from state import EventType, Mood, SetMood, StateStore, AppState
import threading
from soul.moods import load_frames

class OledDisplay:
    def __init__(self):
        serial = i2c(port=1, address=0x3C)
        self.device = ssd1306(serial, width=128, height=64, rotate=0)
        self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)

        self.state_store = StateStore()
        self.state_store.subscribe(EventType.MOOD_CHANGED.value, self._on_mood_changed)
        self.state_store.subscribe(EventType.ENVIRONMENT_CHANGED.value, self._on_env_changed)

        self.current_mood = Mood.NEUTRAL
        
        # Event to wake the animation loop immediately on mood or presence changes
        self._wake_event = threading.Event()

        # Track presence state directly
        self.someone_around = self.state_store.state.someone_around

        # Display starts hidden if nobody is around
        if not self.someone_around:
            try:
                self.device.clear()
                self.device.hide()
            except Exception as e:
                print(f"[oled] Error initializing display state: {e}")

        # Start persistent background animation thread
        self._anim_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self._anim_thread.start()

    def _on_mood_changed(self, mood: Mood) -> None:
        """Non-blocking callback: update state and signal display thread."""
        print(f"[oled] Mood changed to {mood.value}, signaling display thread...")
        self.current_mood = mood
        self._wake_event.set()

    def _on_env_changed(self, app_state: AppState) -> None:
        if app_state.someone_around != self.someone_around:
            print(f"[oled] Presence changed to {app_state.someone_around}")
            self.someone_around = app_state.someone_around
            if self.someone_around:
                try:
                    self.device.show()
                except Exception as e:
                    print(f"[oled] Error showing display: {e}")
            else:
                try:
                    self.device.clear()
                    self.device.hide()
                except Exception as e:
                    print(f"[oled] Error hiding display: {e}")
            self._wake_event.set()

    def _animation_loop(self) -> None:
        """Background thread loop: runs animations only while someone is around."""
        last_mood = None
        frames = []
        idx = 0

        while True:
            # If nobody is around, wait indefinitely until woken up by presence change
            if not self.someone_around:
                self._wake_event.wait()
                self._wake_event.clear()
                continue

            # If mood changed, reload frames
            if self.current_mood != last_mood:
                last_mood = self.current_mood
                try:
                    frames = load_frames(last_mood.value)
                except KeyboardInterrupt:
                    self.device.hide()
                except Exception:
                    frames = [Image.new("1", (128, 64))]
                idx = 0  # Reset animation index

            # Render current frame only when someone is around
            if frames and self.someone_around:
                frame = frames[idx % len(frames)]
                try:
                    self.device.display(frame)
                except KeyboardInterrupt:
                    self.device.hide()
                except Exception:
                    print("[oled] Error displaying frame, skipping...")
                idx += 1

            # Wait 0.5s or wake immediately if mood or presence changes
            self._wake_event.wait(timeout=0.5)
            self._wake_event.clear()

    def display_message(self, message: str) -> None:
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), message, fill="white", font=self.font)
        try:
            self.device.show()
            self.device.display(image)
        except KeyboardInterrupt:
            self.device.hide()
        except Exception:
            pass