from gpiozero import Button
from state import Knob, StateStore, KnobUserAction

class KnobController:
    """Monitors GPIO knob input and dispatches knob button events."""

    def __init__(self) -> None:
        self.state_store = StateStore()
        
        # Imposta bounce_time=0.1 per gestire automaticamente il cooldown nativamente!
        self.btn = Button(17, bounce_time=0.1)
        self.left = Button(27, bounce_time=0.1)
        self.right = Button(22, bounce_time=0.1)

        self.rotation_lock = False
        
        print("[knob] Initializing KnobController")
        self._setup_pins()

    def _setup_pins(self) -> None:
        """Initialize GPIO pins as buttons."""
        try:
            # Assegniamo funzioni SINCRONE
            self.btn.when_pressed = self._btn_down
            self.btn.when_released = self._btn_up
            self.left.when_pressed = self._left_down
            self.right.when_pressed = self._right_down
            self.left.when_released = self._unlock_rotation
            self.right.when_released = self._unlock_rotation
        except Exception as exc:
            print(f"[knob] Error setting up GPIO pins: {exc}")

    def _btn_down(self) -> None:
        # Non serve più logica qui, il bounce_time ignora i falsi contatti.
        # Ho lasciato il metodo nel caso ti servisse in futuro.
        pass

    def _btn_up(self) -> None:
        print("[knob] Dispatching Knob event for btn press")
        # Chiamata sincrona, funziona perfettamente.
        self.state_store.dispatch(Knob(KnobUserAction.PRESS))

    def _left_down(self) -> None:
        if self.rotation_lock:
            return
        self.rotation_lock = True
        print("[knob] Dispatching Knob event for left rotation")
        self.state_store.dispatch(Knob(KnobUserAction.TURN_LEFT))
    
    def _right_down(self) -> None:
        if self.rotation_lock:
            return
        self.rotation_lock = True
        print("[knob] Dispatching Knob event for right rotation")
        self.state_store.dispatch(Knob(KnobUserAction.TURN_RIGHT))
    
    def _unlock_rotation(self) -> None:
        self.rotation_lock = False