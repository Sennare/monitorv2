from gpiozero import Button
from state import Knob, StateStore, KnobUserAction, SetSomeoneAround
import threading

MOVEMENT_TIMEOUT_SECONDS = 60

class Movement:

    def __init__(self) -> None:
        self.state_store = StateStore()
        self.movement_sensor = Button(11, bounce_time=0.1, pull_up=False)
        
        # Inizializziamo una variabile per tenere traccia del timer
        self._no_movement_timer: threading.Timer | None = None
        # Un lock per evitare race condition sul timer tra thread diversi
        self._lock = threading.Lock()

        print("[movement] Initializing Movement")
        self._setup_pins()

    def _setup_pins(self) -> None:
        """Initialize GPIO pins as buttons."""
        try:
            # Assegniamo funzioni SINCRONE
            self.movement_sensor.when_pressed = self._movement_detected
        except Exception as exc:
            print(f"[movement] Error setting up GPIO pins: {exc}")
    
    def _movement_detected(self) -> None:
        if not self._no_movement_timer:
            print("[movement] Movement detected, dispatching SetSomeoneAround event")
            self.state_store.dispatch(SetSomeoneAround(True))
        
        # Gestione del timer per l'assenza di movimento
        with self._lock:
            # Se c'era già un timer attivo (es. l'utente si è mosso 10 secondi fa), lo cancelliamo
            if self._no_movement_timer is not None:
                self._no_movement_timer.cancel()
            
            # Fatto partire un nuovo timer da MOVEMENT_TIMEOUT_SECONDS secondi
            self._no_movement_timer = threading.Timer(MOVEMENT_TIMEOUT_SECONDS, self._no_movement_timeout)
            self._no_movement_timer.start()

    def _no_movement_timeout(self) -> None:
        print(f"[movement] No movement detected for {MOVEMENT_TIMEOUT_SECONDS} seconds, dispatching False event")
        self.state_store.dispatch(SetSomeoneAround(False))
        
        with self._lock:
            self._no_movement_timer = None