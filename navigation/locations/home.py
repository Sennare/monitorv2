import board
import busio

from ..abstract_location import AbstractLocation
from state import StateStore, EventType
from display.lcd_core import LCDCore


class Home(AbstractLocation):
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
        self.lcd.set_background_color((28, 20, 36))
        self.lcd.write_rows(
            [
                "✨ Welcome home!",
                "You are looking lovely today!",
                "Ready for some fun?",
                "Have a cozy day!",
            ],
            bg_color=(28, 20, 36),
            text_color=(255, 245, 240),
            font_size=18,
            bold=False,
            margin_y=30,
            line_spacing=10,
        )