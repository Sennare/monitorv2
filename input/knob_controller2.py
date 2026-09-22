import os
import threading
from typing import Optional
from state import Knob, StateStore, KnobUserAction

try:
    from gpiozero import Button, RotaryEncoder
    GPIOZERO_AVAILABLE = True
except (ImportError, NotImplementedError):
    GPIOZERO_AVAILABLE = False
    Button = None
    RotaryEncoder = None


class KnobController:
    """
    Hardware Rotary Encoder & Push Button Controller.
    Utilizes quadrature rotary decoding (via gpiozero.RotaryEncoder)
    to reliably capture every rotation step without missing detents or direction reversal.
    """

    def __init__(
        self,
        pin_btn: int = 17,
        pin_a: int = 27,
        pin_b: int = 22,
        steps_per_detent: Optional[int] = None,
        inverted: bool = False,
        bounce_time: Optional[float] = None,
    ) -> None:
        self.state_store = StateStore()
        self.pin_btn = pin_btn
        self.pin_a = pin_a
        self.pin_b = pin_b
        self.inverted = inverted
        self.bounce_time = bounce_time

        # Configurable steps per detent (defaults to 1, or can be set via env var or param)
        # Most mechanical encoders (e.g. KY-040) output 1, 2, or 4 steps per physical click.
        if steps_per_detent is not None:
            self.steps_per_detent = max(1, steps_per_detent)
        else:
            env_steps = os.environ.get("KNOB_STEPS_PER_DETENT")
            self.steps_per_detent = max(1, int(env_steps)) if env_steps else 1

        self._lock = threading.Lock()
        self._last_steps = 0

        self.btn: Optional[Button] = None
        self.rotor: Optional[RotaryEncoder] = None

        print(
            f"[knob] Initializing KnobController (btn={pin_btn}, A={pin_a}, B={pin_b}, "
            f"steps_per_detent={self.steps_per_detent}, bounce_time={self.bounce_time})"
        )
        self._setup_hardware()

    def _setup_hardware(self) -> None:
        """Initializes gpiozero Button and RotaryEncoder."""
        if not GPIOZERO_AVAILABLE:
            print("[knob] gpiozero not available, operating in mock mode.")
            return

        try:
            # 1. Push Button on GPIO 17 with 50ms tactile debounce
            self.btn = Button(self.pin_btn, bounce_time=0.05)
            self.btn.when_pressed = self._btn_pressed

            # 2. Quadrature Rotary Encoder on GPIO 27 (A/CLK) and GPIO 22 (B/DT)
            # Quadrature decoding inherently filters single-pin bounce.
            # wrap=False ensures raw cumulative step counting.
            self.rotor = RotaryEncoder(
                self.pin_a,
                self.pin_b,
                wrap=False,
                bounce_time=self.bounce_time,
            )
            self._last_steps = self.rotor.steps
            self.rotor.when_rotated = self._on_rotated

            print(f"[knob] Hardware initialized: initial rotor steps={self._last_steps}")
        except Exception as exc:
            print(f"[knob] Error setting up rotary encoder pins: {exc}")

    def _btn_pressed(self) -> None:
        """Callback fired immediately upon button press."""
        print("[knob] Physical button pressed, dispatching Knob(PRESS)")
        self.state_store.dispatch(Knob(KnobUserAction.PRESS))

    def _on_rotated(self) -> None:
        """
        Callback fired on quadrature edge transitions.
        Accumulates delta steps to prevent dropped steps during rapid rotation.
        """
        if self.rotor is None:
            return

        with self._lock:
            current_steps = self.rotor.steps
            delta = current_steps - self._last_steps

            if abs(delta) >= self.steps_per_detent:
                steps_to_dispatch = delta // self.steps_per_detent
                self._last_steps += steps_to_dispatch * self.steps_per_detent

                direction = 1 if steps_to_dispatch > 0 else -1
                if self.inverted:
                    direction = -direction

                action = KnobUserAction.TURN_RIGHT if direction > 0 else KnobUserAction.TURN_LEFT
                for _ in range(abs(steps_to_dispatch)):
                    print(f"[knob] Rotation step detected, dispatching Knob({action.value})")
                    self.state_store.dispatch(Knob(action))

    def simulate_turn_right(self, count: int = 1) -> None:
        """Helper for test suites or simulation."""
        for _ in range(count):
            self.state_store.dispatch(Knob(KnobUserAction.TURN_RIGHT))

    def simulate_turn_left(self, count: int = 1) -> None:
        """Helper for test suites or simulation."""
        for _ in range(count):
            self.state_store.dispatch(Knob(KnobUserAction.TURN_LEFT))

    def simulate_press(self) -> None:
        """Helper for test suites or simulation."""
        self.state_store.dispatch(Knob(KnobUserAction.PRESS))

    def close(self) -> None:
        """Releases GPIO hardware pins."""
        if self.btn is not None:
            try:
                self.btn.close()
            except Exception:
                pass
        if self.rotor is not None:
            try:
                self.rotor.close()
            except Exception:
                pass