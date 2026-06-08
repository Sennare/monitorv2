import asyncio
from gpiozero import Button
from state import KnobBtnPressed, StateStore

DEFAULT_PINS = (17, 27, 22)
COOLDOWN_SECONDS = 0.1


class KnobController:
    """Monitors GPIO knob input and dispatches knob button events."""

    def __init__(self, pins: tuple[int, ...] = DEFAULT_PINS) -> None:
        self.pins = pins
        self.buttons: dict[int, Button] = {}
        self.pin_states: dict[int, str] = {}
        self.pin_cooldowns: dict[int, int] = {}
        self.state_store = StateStore()
        self.loop: asyncio.AbstractEventLoop | None = None

        print("[knob] Initializing KnobController")
        self._setup_pins()

    def _setup_pins(self) -> None:
        """Initialize GPIO pins as buttons."""
        try:
            for pin in self.pins:
                button = Button(pin)
                button.when_pressed = lambda p=pin: self._schedule_pin_change(p, "HIGH")
                button.when_released = lambda p=pin: self._schedule_pin_change(p, "LOW")
                self.buttons[pin] = button
                self.pin_states[pin] = "LOW" if not button.is_pressed else "HIGH"
                self.pin_cooldowns[pin] = 0
                print(f"[knob] GPIO {pin} initialized - initial state: {self.pin_states[pin]}")
        except Exception as exc:
            print(f"[knob] Error setting up GPIO pins: {exc}")

    async def _on_pin_change(self, pin: int, new_state: str) -> None:
        """Process a GPIO pin transition event."""
        old_state = self.pin_states.get(pin, "UNKNOWN")
        if old_state == new_state:
            return

        self.pin_states[pin] = new_state
        print(f"[knob] GPIO {pin} changed: {old_state} -> {new_state}")

        if self.pin_cooldowns.get(pin, 0) != 0:
            return

        self.pin_cooldowns[pin] = 1
        asyncio.create_task(self._reset_cooldown(pin))

        if pin == 17 and new_state == "HIGH":
            print("[knob] Dispatching KnobBtnPressed event")
            self.state_store.dispatch(KnobBtnPressed())

    async def _reset_cooldown(self, pin: int) -> None:
        await asyncio.sleep(COOLDOWN_SECONDS)
        self.pin_cooldowns[pin] = 0

    def _schedule_pin_change(self, pin: int, new_state: str) -> None:
        """Schedule the pin-change coroutine on the configured event loop."""
        if self.loop is None:
            print("[knob] Event loop not ready, ignoring pin event")
            return

        self.loop.call_soon_threadsafe(
            self.loop.create_task,
            self._on_pin_change(pin, new_state),
        )

    async def start_worker(self) -> None:
        """Begin the GPIO monitor worker and capture the running event loop."""
        self.loop = asyncio.get_running_loop()
        print("[knob] GPIO monitoring worker started")

        try:
            while True:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            print("[knob] GPIO monitoring worker stopped")
            self.cleanup()
            raise

    def cleanup(self) -> None:
        """Release GPIO resources."""
        print("[knob] Cleaning up GPIO pins")

        try:
            for button in self.buttons.values():
                button.close()
        except Exception as exc:
            print(f"[knob] Error during cleanup: {exc}")
