from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
from state import Mood
import threading
from soul.moods import load_frames
import asyncio

class MoodDemo:
    def __init__(self):
        serial = i2c(port=1, address=0x3C)
        self.device = ssd1306(serial, width=128, height=64, rotate=0)
        self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        
        # Unico evento per svegliare il thread immediatamente se il mood cambia
        self._mood_changed_event = threading.Event()

        self.mood = Mood.NEUTRAL.value
        
        # Avvia un UNICO thread persistente in background
        print(f"Starting anim")
        self.device.show()
        self._anim_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self._anim_thread.start()

    def _animation_loop(self) -> None:
        """Loop infinito del thread in background."""
        last_mood = None
        frames = []
        idx = 0

        while True:
            frames = load_frames(self.mood)

            # Rendering del frame corrente
            if frames:
                frame = frames[idx % len(frames)]
                try:
                    self.device.display(frame)
                except KeyboardInterrupt:
                    self.device.hide()
                except Exception:
                    print("[oled] Error displaying frame, skipping...")
                idx += 1
            
            if (idx > 8):
                idx = 0

            # TRUCCO CHIAVE: Invece di time.sleep(0.5), aspettiamo l'evento.
            # Se l'evento viene attivato (set), il wait si interrompe SUBITO.
            # Se non viene attivato, aspetta 0.5 secondi (il tuo framerate).
            self._mood_changed_event.wait(timeout=0.5)
            self._mood_changed_event.clear()

class Application:
    def __init__(self):
        self.demo = MoodDemo()

        print("[app] Initializing application")

    async def run(self) -> None:
        print("[app] Starting monitor application...")
        
        while True:
            await asyncio.sleep(1)


async def main() -> None:
    app = Application()
    await app.run()
    await asyncio.sleep(10)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication stopped")
    except Exception as e:
        print(f"Fatal error: {e}")