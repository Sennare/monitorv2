from ..abstract_location import AbstractLocation
from state import StateStore, EventType
from display.lcd_core import LCDCore
from display.animations.welcome import CuteCiaoAnimation


class Home(AbstractLocation):
    def __init__(self, use_main_lcd=True):
        self.state_store = StateStore()
        # Inizializzazione super pulita!
        display = LCDCore()

        # Creazione e avvio dell'animazione
        animazione_demo = CuteCiaoAnimation()
        display.play_animation(animazione_demo, frame_delay=1, cycles=4)
        # self.state_store.subscribe(EventType.MOOD_CHANGED.value, self._on_mood_changed)

    def render(self):
        return