from ..abstract_location import AbstractLocation
from display.lcd_core import LCDCore
from display.animations.welcome import CuteCiaoAnimation
from state import AppState, KnobUserAction
from typing import Optional, Callable


class WelcomePage(AbstractLocation):
    """
    Startup Welcome screen: plays a cute greeting animation and
    automatically transitions to the HomePage when finished or on user knob interaction.
    """

    def __init__(self, on_complete_callback: Optional[Callable[[], None]] = None):
        self._on_complete_callback = on_complete_callback
        self._animation = CuteCiaoAnimation()
        self._is_active = False

    def on_enter(self) -> None:
        self._is_active = True

    def on_exit(self) -> None:
        self._is_active = False

    def render(self, lcd: LCDCore, state: AppState) -> None:
        # Play the welcome animation for 2 cycles (approx 2.4s)
        lcd.play_animation(
            self._animation,
            frame_delay=0.4,
            cycles=2,
            on_complete=self._handle_complete,
        )

    def _handle_complete(self) -> None:
        if self._is_active and self._on_complete_callback:
            self._on_complete_callback()

    def handle_knob(self, action: KnobUserAction) -> Optional[str]:
        # User skipped welcome by touching knob
        return "HOME"
