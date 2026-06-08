from ..abstract_location import AbstractLocation
from state import StateStore, EventType
from display.lcd import Lcd

class Home(AbstractLocation):
    def __init__(self):
        self.state_store = StateStore()
        self.lcd = Lcd()
        # self.state_store.subscribe(EventType.MOOD_CHANGED.value, self._on_mood_changed)

    def render(self):
        self.lcd.clear()
        self.lcd.write(line2 = "Welcome!")