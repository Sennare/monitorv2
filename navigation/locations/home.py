from ..abstract_location import AbstractLocation
from state import StateStore, EventType
from display.lcd_core import LCDCore
from display.animations.welcome import CuteCiaoAnimation


class Home(AbstractLocation):
    def __init__(self, use_main_lcd=True):
        self.state_store = StateStore()
        # Inizializzazione super pulita!
        self.lcd = LCDCore()

        # Creazione e avvio dell'animazione.
        # Eseguiamo una singola ripetizione con un delay realistico: la vecchia
        # configurazione (cycles=4) e il loop sincrono bloccavano l'intero flusso
        # e facevano sembrare le transizioni molto più lente del previsto.
        animazione_demo = CuteCiaoAnimation()
        self.lcd.play_animation(animazione_demo, frame_delay=1, cycles=6)
        # self.state_store.subscribe(EventType.MOOD_CHANGED.value, self._on_mood_changed)

    def render(self):
        return