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
        
        # Unico evento per svegliare il thread immediatamente se il mood cambia
        self._mood_changed_event = threading.Event()
        
        # Avvia un UNICO thread persistente in background
        self._anim_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self._anim_thread.start()

    def _on_mood_changed(self, mood: Mood) -> None:
        """Callback non bloccante: aggiorna lo stato e sveglia il thread."""
        print(f"[oled] Mood changed to {mood.value}, signaling display thread...")
        self.current_mood = mood
        self._mood_changed_event.set() # Interrompe immediatamente il time.sleep del thread

    def _on_env_changed(self, app_state: AppState) -> None:
        if (app_state.someone_around):
            self.device.show()
        else:
            self.device.hide()

    def _animation_loop(self) -> None:
        """Loop infinito del thread in background."""
        last_mood = None
        frames = []
        idx = 0

        while True:
            # Se il mood è cambiato rispetto all'ultimo ciclo, ricarica i frame
            if self.current_mood != last_mood:
                last_mood = self.current_mood
                try:
                    frames = load_frames(last_mood.value)
                except KeyboardInterrupt:
                    self.device.hide()
                except Exception:
                    frames = [Image.new("1", (128, 64))]
                idx = 0 # Resetta l'indice dell'animazione

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

            # TRUCCO CHIAVE: Invece di time.sleep(0.5), aspettiamo l'evento.
            # Se l'evento viene attivato (set), il wait si interrompe SUBITO.
            # Se non viene attivato, aspetta 0.5 secondi (il tuo framerate).
            self._mood_changed_event.wait(timeout=0.5)
            self._mood_changed_event.clear()

    def display_message(self, message: str) -> None:
        # Nota: se usi questo metodo, potresti voler sospendere temporaneamente il loop dell'animazione
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), message, fill="white", font=self.font)
        try:
            self.device.display(image)
        except KeyboardInterrupt:
            self.device.hide()
        except Exception:
            pass