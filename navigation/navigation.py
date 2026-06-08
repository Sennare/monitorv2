from state import EventType, Mood, SetMood, StateStore
from enum import Enum
from .abstract_location import AbstractLocation
from .locations.home import Home
from .locations.menu import Menu

class Location(Enum):
    HOME = "home"
    MAIN_MENU = "main_menu"

class Navigation:
    def __init__(self):
        self.location = Location.HOME
        self.state_store = StateStore()
        self.current_location : AbstractLocation = Home()
        self.state_store.subscribe(EventType.KNOB_BTN_PRESSED.value, self._on_knob_btn_pressed)
        self.render()

    def _on_knob_btn_pressed(self, new_mood: Mood) -> None:
        if self.location == Location.HOME:
            self.location = Location.MAIN_MENU
            self.current_location = Menu()
        else:
            self.location = Location.HOME
            self.current_location = Home()
        self.render()

    def render(self):
        self.current_location.render()