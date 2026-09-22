import threading
from enum import Enum
from typing import Dict, Optional

from state import EventType, StateStore, AppState, KnobUserAction
from display.lcd_core import LCDCore
from .abstract_location import AbstractLocation
from .locations.welcome_page import WelcomePage
from .locations.home import Home
from .locations.menu import Menu
from .locations.settings import Settings
from .locations.sensors_page import SensorsPage


class Location(str, Enum):
    WELCOME = "WELCOME"
    HOME = "HOME"
    MENU = "MENU"
    SETTINGS = "SETTINGS"
    SENSORS = "SENSORS"


class Navigation:
    """
    Central UI Navigator & Page Manager.
    Coordinates active page rendering on LCDCore, routes rotary encoder events,
    and manages the 45-second inactivity display sleep/wake lifecycle.
    """

    def __init__(self, start_with_welcome: bool = True):
        self._lock = threading.RLock()
        self.state_store = StateStore()
        self.lcd = LCDCore()

        # Page instances registry
        self.pages: Dict[str, AbstractLocation] = {
            Location.WELCOME.value: WelcomePage(
                on_complete_callback=lambda: self.navigate_to(Location.HOME.value)
            ),
            Location.HOME.value: Home(),
            Location.MENU.value: Menu(),
            Location.SETTINGS.value: Settings(),
            Location.SENSORS.value: SensorsPage(),
        }

        # Set initial location
        initial_loc = Location.WELCOME.value if start_with_welcome else Location.HOME.value
        self.current_location_id: str = initial_loc
        self.current_page: AbstractLocation = self.pages[initial_loc]

        # Subscribe to rotary knob events
        self._unsubscribers = [
            self.state_store.subscribe(EventType.KNOB.value, self._on_knob_interacted),
            self.state_store.subscribe(EventType.ENVIRONMENT_CHANGED.value, self._on_telemetry_updated),
            self.state_store.subscribe(EventType.MOOD_CHANGED.value, self._on_mood_updated),
        ]

        # Start initial page lifecycle
        self.current_page.on_enter()
        self.render()

    def close(self) -> None:
        """Clean up subscribers and stop any animations."""
        self.lcd.stop_animation()
        for unsub in self._unsubscribers:
            try:
                unsub()
            except Exception:
                pass
        self._unsubscribers.clear()

    def navigate_to(self, target_location: str) -> None:
        """Transitions from current page to target page cleanly."""
        target_key = target_location.upper()
        if target_key not in self.pages:
            print(f"[nav] Unknown target location: {target_location}, falling back to HOME")
            target_key = Location.HOME.value

        with self._lock:
            if target_key == self.current_location_id:
                return

            print(f"[nav] Navigating: {self.current_location_id} -> {target_key}")

            # 1. Exit current page & stop any active animations
            self.current_page.on_exit()
            self.lcd.stop_animation()

            # 2. Switch to new page
            self.current_location_id = target_key
            self.current_page = self.pages[target_key]

            # 3. Enter new page
            self.current_page.on_enter()

            # 4. Render new page & keep display awake
            self.render()

    def _on_knob_interacted(self, action: Optional[KnobUserAction]) -> None:
        """
        Handles physical rotary encoder events (PRESS, TURN_LEFT, TURN_RIGHT).
        Implements display wakeup on first touch when sleeping, or routes to active page.
        """
        # If payload was not provided, default to PRESS
        if action is None:
            action = KnobUserAction.PRESS

        with self._lock:
            # If screen is currently off, turn it on and wake up without triggering accidental actions
            if not self.lcd.is_screen_on:
                print("[nav] Knob interacted while display sleeping. Waking up display.")
                if hasattr(self.current_page, "reset_time_travel"):
                    self.current_page.reset_time_travel()
                self.lcd.turn_on()
                self.render()
                return

            # Display is awake: reset the 45s timer on every interaction
            self.lcd.reset_inactivity_timer()

            # Pass interaction to the active page
            target_location = self.current_page.handle_knob(action)

        if target_location is not None:
            self.navigate_to(target_location)
        else:
            with self._lock:
                self.render()

    def _on_telemetry_updated(self, state: AppState) -> None:
        """Refreshes live metrics on screen if the display is currently on."""
        with self._lock:
            if not self.lcd.is_screen_on:
                return
            # Only live-update pages that display environmental metrics
            if self.current_location_id in (Location.HOME.value, Location.SENSORS.value):
                self.render()

    def _on_mood_updated(self, mood) -> None:
        """Refreshes mood badge if display is on and home page is active."""
        with self._lock:
            if not self.lcd.is_screen_on:
                return
            if self.current_location_id == Location.HOME.value:
                self.render()

    def render(self) -> None:
        """Paints current page to LCD using current AppState."""
        try:
            self.current_page.render(self.lcd, self.state_store.state)
        except Exception as e:
            print(f"[nav] Render error on page {self.current_location_id}: {e}")