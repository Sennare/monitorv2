from gpiozero import Button
from state import StateStore, SetSomeoneAround
import threading

MOVEMENT_TIMEOUT_SECONDS = 60

class Movement:

    def __init__(self) -> None:
        self.state_store = StateStore()
        self.movement_sensor = Button(5, bounce_time=0.1, pull_up=False)
        
        # Timer tracking absence after movement
        self._no_movement_timer: threading.Timer | None = None
        self._lock = threading.Lock()

        print("[movement] Initializing Movement")
        self._setup_pins()

        # Check initial sensor status on startup
        try:
            if self.movement_sensor.is_pressed:
                print("[movement] Sensor active on startup, dispatching True")
                self._movement_detected()
            else:
                print("[movement] Sensor inactive on startup, dispatching False")
                self.state_store.dispatch(SetSomeoneAround(False))
        except Exception as exc:
            print(f"[movement] Error evaluating initial sensor state: {exc}")

    def _setup_pins(self) -> None:
        """Initialize GPIO pins as buttons."""
        try:
            self.movement_sensor.when_pressed = self._movement_detected
        except Exception as exc:
            print(f"[movement] Error setting up GPIO pins: {exc}")
    
    def _movement_detected(self) -> None:
        if not self.state_store.state.someone_around:
            print("[movement] Movement detected, dispatching SetSomeoneAround event")
            self.state_store.dispatch(SetSomeoneAround(True))
        
        # Reset inactivity timer
        with self._lock:
            if self._no_movement_timer is not None:
                self._no_movement_timer.cancel()
            
            self._no_movement_timer = threading.Timer(MOVEMENT_TIMEOUT_SECONDS, self._no_movement_timeout)
            self._no_movement_timer.start()

    def _no_movement_timeout(self) -> None:
        with self._lock:
            # If sensor is still actively triggered, re-arm timer instead of declaring absence
            try:
                if self.movement_sensor.is_pressed:
                    print("[movement] Sensor still active, extending absence timer")
                    self._no_movement_timer = threading.Timer(MOVEMENT_TIMEOUT_SECONDS, self._no_movement_timeout)
                    self._no_movement_timer.start()
                    return
            except Exception as exc:
                print(f"[movement] Error checking sensor in timeout: {exc}")

            print(f"[movement] No movement detected for {MOVEMENT_TIMEOUT_SECONDS} seconds, dispatching False event")
            self._no_movement_timer = None

        if self.state_store.state.someone_around:
            self.state_store.dispatch(SetSomeoneAround(False))