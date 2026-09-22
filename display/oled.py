import time
import threading
from PIL import Image, ImageDraw, ImageFont
from state import EventType, Mood, SetMood, StateStore, AppState
from soul.moods import load_frames
try:
    from luma.core.interface.serial import i2c
    from luma.oled.device import ssd1306
    OLED_HARDWARE_AVAILABLE = True
except (ImportError, NotImplementedError):
    i2c = None
    ssd1306 = None
    OLED_HARDWARE_AVAILABLE = False


class _MockOledDevice:
    def __init__(self, width=128, height=64):
        self.width = width
        self.height = height
        self.is_hidden = False
        self.last_frame = None

    def clear(self):
        pass

    def hide(self):
        self.is_hidden = True

    def show(self):
        self.is_hidden = False

    def display(self, frame):
        self.last_frame = frame


DEFAULT_FPS = 20.0

class OledDisplay:
    def __init__(self, fps: float = DEFAULT_FPS):
        self.fps = float(fps)
        self.frame_delay = 1.0 / self.fps

        if OLED_HARDWARE_AVAILABLE and i2c and ssd1306:
            try:
                serial = i2c(port=1, address=0x3C)
                self.device = ssd1306(serial, width=128, height=64, rotate=0)
            except Exception as e:
                print(f"[oled] Hardware init failed ({e}), using mock device")
                self.device = _MockOledDevice(width=128, height=64)
        else:
            self.device = _MockOledDevice(width=128, height=64)

        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except Exception:
            self.font = ImageFont.load_default()

        self.state_store = StateStore()
        self._unsubscribers = [
            self.state_store.subscribe(EventType.MOOD_CHANGED.value, self._on_mood_changed),
            self.state_store.subscribe(EventType.ENVIRONMENT_CHANGED.value, self._on_env_changed),
        ]

        self.current_mood = Mood.NEUTRAL
        
        # Event to wake the animation loop immediately on mood or presence changes
        self._wake_event = threading.Event()
        self._stop_event = threading.Event()
        self._is_closed = False

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
        if self._stop_event.is_set():
            return
        print(f"[oled] Mood changed to {mood.value}, signaling display thread...")
        self.current_mood = mood
        self._wake_event.set()

    def _on_env_changed(self, app_state: AppState) -> None:
        if self._stop_event.is_set():
            return
        if app_state.someone_around != self.someone_around:
            print(f"[oled] Presence changed to {app_state.someone_around}")
            self.someone_around = app_state.someone_around
            if self.someone_around:
                try:
                    self.device.show()
                except Exception as e:
                    if not self._stop_event.is_set():
                        print(f"[oled] Error showing display: {e}")
            else:
                try:
                    self.device.clear()
                    self.device.hide()
                except Exception as e:
                    if not self._stop_event.is_set():
                        print(f"[oled] Error hiding display: {e}")
            self._wake_event.set()

    def _animation_loop(self) -> None:
        """Background thread loop: runs animations only while someone is around."""
        last_mood = None
        frames = []
        idx = 0

        while not self._stop_event.is_set():
            # If nobody is around, wait indefinitely until woken up by presence change or stop
            if not self.someone_around:
                self._wake_event.wait(timeout=0.5)
                self._wake_event.clear()
                continue

            # If mood changed, reload frames
            if self.current_mood != last_mood:
                last_mood = self.current_mood
                try:
                    frames = load_frames(last_mood.value)
                except KeyboardInterrupt:
                    try:
                        self.device.hide()
                    except Exception:
                        pass
                    break
                except Exception:
                    frames = [Image.new("1", (128, 64))]
                idx = 0  # Reset animation index

            start_time = time.monotonic()

            # Render current frame only when someone is around
            if frames and self.someone_around and not self._stop_event.is_set():
                frame = frames[idx % len(frames)]
                try:
                    self.device.display(frame)
                except KeyboardInterrupt:
                    try:
                        self.device.hide()
                    except Exception:
                        pass
                    break
                except Exception:
                    if not self._stop_event.is_set():
                        try:
                            print("[oled] Error displaying frame, skipping...")
                        except Exception:
                            pass
                idx += 1

            if self._stop_event.is_set():
                break

            # Wait remaining duration to maintain target FPS, or wake immediately on event
            elapsed = time.monotonic() - start_time
            sleep_time = max(0.001, self.frame_delay - elapsed)
            self._wake_event.wait(timeout=sleep_time)
            self._wake_event.clear()

    def display_message(self, message: str) -> None:
        if self._stop_event.is_set():
            return
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), message, fill="white", font=self.font)
        try:
            self.device.show()
            self.device.display(image)
        except KeyboardInterrupt:
            try:
                self.device.hide()
            except Exception:
                pass
        except Exception:
            pass

    def close(self) -> None:
        """Stops the animation thread, unsubscribes events, and blanks display."""
        if self._is_closed:
            return
        self._is_closed = True
        self._stop_event.set()
        self._wake_event.set()

        for unsub in self._unsubscribers:
            try:
                unsub()
            except Exception:
                pass
        self._unsubscribers.clear()

        if hasattr(self, "_anim_thread") and self._anim_thread.is_alive() and threading.current_thread() != self._anim_thread:
            self._anim_thread.join(timeout=1.0)

        try:
            self.device.clear()
            self.device.hide()
        except Exception:
            pass