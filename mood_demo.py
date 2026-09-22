try:
    from luma.core.interface.serial import i2c
    from luma.oled.device import ssd1306
    OLED_HARDWARE_AVAILABLE = True
except (ImportError, NotImplementedError):
    i2c = None
    ssd1306 = None
    OLED_HARDWARE_AVAILABLE = False

from PIL import Image, ImageDraw, ImageFont
from state import Mood
import threading
from soul.moods import load_frames
import asyncio

class _MockOledDevice:
    def __init__(self, width=128, height=64):
        self.width = width
        self.height = height

    def clear(self): pass
    def hide(self): pass
    def show(self): pass
    def display(self, frame): pass

class MoodDemo:
    def __init__(self):
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
        
        # Unico evento per svegliare il thread immediatamente se il mood cambia
        self._mood_changed_event = threading.Event()
        self._stop_event = threading.Event()
        self._is_closed = False

        self.mood = Mood.NEUTRAL.value
        
        self.fps = 20.0
        self.frame_delay = 1.0 / self.fps

        # Avvia un UNICO thread persistente in background
        print(f"Starting anim at {self.fps} FPS")
        self.device.show()
        self._anim_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self._anim_thread.start()

    def _animation_loop(self) -> None:
        """Loop del thread in background a 20 FPS."""
        last_mood = None
        frames = []
        idx = 0

        while not self._stop_event.is_set():
            if self.mood != last_mood:
                last_mood = self.mood
                frames = load_frames(self.mood)
                idx = 0

            # Rendering del frame corrente
            if frames and not self._stop_event.is_set():
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
                idx = (idx + 1) % len(frames)

            if self._stop_event.is_set():
                break

            # Aspetta frame_delay (es. 0.05s per 20 FPS) o sveglia subito se il mood cambia
            self._mood_changed_event.wait(timeout=self.frame_delay)
            self._mood_changed_event.clear()

    def close(self) -> None:
        if self._is_closed:
            return
        self._is_closed = True
        self._stop_event.set()
        self._mood_changed_event.set()
        if hasattr(self, "_anim_thread") and self._anim_thread.is_alive() and threading.current_thread() != self._anim_thread:
            self._anim_thread.join(timeout=1.0)
        try:
            self.device.clear()
            self.device.hide()
        except Exception:
            pass


class Application:
    def __init__(self):
        self.demo = MoodDemo()
        self._is_closed = False

        print("[app] Initializing application")

    async def run(self) -> None:
        print("[app] Starting monitor application...")
        while True:
            await asyncio.sleep(1)

    def close(self) -> None:
        if self._is_closed:
            return
        self._is_closed = True
        if hasattr(self, "demo") and self.demo is not None:
            self.demo.close()


async def main() -> None:
    app = None
    try:
        app = Application()
        await app.run()
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        if app is not None:
            app.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
        print("\nApplication stopped")
    except KeyboardInterrupt:
        print("\nApplication stopped")
    except Exception as e:
        print(f"Fatal error: {e}")