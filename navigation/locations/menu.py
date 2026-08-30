import board
import busio
import digitalio

from ..abstract_location import AbstractLocation
from state import StateStore, EventType
from display.lcd_core import LCDCore

class Menu(AbstractLocation):
    def __init__(self, use_main_lcd=True):
        self.state_store = StateStore()
        spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        self.lcd = LCDCore(
            spi=spi,
            cs_pin=board.D8,
            dc_pin=board.D24,
            rst_pin=board.D13,
            bl_pin=board.D6
        )
        # self.state_store.subscribe(EventType.MOOD_CHANGED.value, self._on_mood_changed)

    def render(self):
        self.lcd.set_background_color((18, 30, 45))
        self.lcd.write_rows(
            [
                "☰ Menu",
                "• settings",
                "• sensors",
                "• display",
                "• system",
                "• back",
            ],
            bg_color=(18, 30, 45),
            text_color=(220, 240, 255),
            font_size=18,
            bold=False,
            margin_y=20,
            line_spacing=8,
        )