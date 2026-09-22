from abc import ABC, abstractmethod
from typing import Optional
from state import AppState, KnobUserAction
from display.lcd_core import LCDCore


class AbstractLocation(ABC):
    """
    Abstract base class for all LCD UI locations / pages.
    """

    @abstractmethod
    def render(self, lcd: LCDCore, state: AppState) -> None:
        """Renders the page to the provided LCD display."""
        pass

    def handle_knob(self, action: KnobUserAction) -> Optional[str]:
        """
        Processes rotary encoder input (TURN_LEFT, TURN_RIGHT, PRESS).
        Returns target Location name (string) if a navigation transition should occur,
        or None if the event was consumed internally.
        """
        return None

    def on_enter(self) -> None:
        """Called when this page becomes active."""
        pass

    def on_exit(self) -> None:
        """Called when leaving this page."""
        pass