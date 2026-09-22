from ..abstract_location import AbstractLocation
from state import StateStore, EventType
from display.lcd_core import LCDCore
from display.animations.cat_blink import CuteCatBlinkAnimation

class Menu(AbstractLocation):
    def __init__(self, use_main_lcd=True):
        self.state_store = StateStore()
        # Inizializzazione super pulita!
        self.lcd = LCDCore()
        # self.state_store.subscribe(EventType.MOOD_CHANGED.value, self._on_mood_changed)
        animazione_demo = CuteCatBlinkAnimation()
        self.lcd.play_animation(animazione_demo, frame_delay=0.5, cycles=6)

    def render(self):
        return
        # self.lcd.set_background_color((18, 30, 45))
        # self.lcd.write_rows(
        #     [
        #         "☰ Menu",
        #         "• settings",
        #         "• sensors",
        #         "• display",
        #         "• system",
        #         "• back",
        #     ],
        #     bg_color=(18, 30, 45),
        #     text_color=(220, 240, 255),
        #     font_size=18,
        #     bold=False,
        #     margin_y=20,
        #     line_spacing=8,
        # )