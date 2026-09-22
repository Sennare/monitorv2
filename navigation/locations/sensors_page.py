from PIL import Image, ImageDraw
from ..abstract_location import AbstractLocation
from display.lcd_core import LCDCore
from state import AppState, KnobUserAction, StateStore, BoostEmotion, Mood
from typing import Optional


class SensorsPage(AbstractLocation):
    """
    Detailed telemetry and hardware sensors monitor.
    Entering triggers a CURIOUS emotion on the soul.
    """

    def __init__(self):
        self.state_store = StateStore()

    def on_enter(self) -> None:
        self.state_store.dispatch(BoostEmotion(Mood.CURIOUS, 60))

    def render(self, lcd: LCDCore, state: AppState) -> None:
        img = Image.new("RGB", (lcd.width, lcd.height), (15, 23, 42))
        draw = ImageDraw.Draw(img)

        font_title = lcd._get_font(size=15, bold=True)
        font_label = lcd._get_font(size=11, bold=False)
        font_value = lcd._get_font(size=15, bold=True)
        font_hint = lcd._get_font(size=11, italic=True)

        # --- Header ---
        draw.rectangle((0, 0, lcd.width, 42), fill=(30, 41, 59))
        draw.text((15, 12), "📊 SENSORS & TELEMETRY", font=font_title, fill=(56, 189, 248))
        draw.line([(0, 42), (lcd.width, 42)], fill=(71, 85, 105), width=2)

        # Metrics list
        metrics = [
            ("AHT20 AMBIENT TEMP", f"{state.temperature:.2f} °C" if state.temperature else "--.- °C", (251, 146, 60)),
            ("AHT20 HUMIDITY", f"{state.humidity:.2f} %" if state.humidity else "--.- %", (56, 189, 248)),
            ("PIR MOTION SENSOR", "Motion Active" if state.someone_around else "No Motion (Idle)", (74, 222, 128) if state.someone_around else (148, 163, 184)),
            ("DATABASE PERSISTENCE", "PostgreSQL (15m interval)", (192, 132, 252)),
            ("LCD POWER MANAGEMENT", "Auto Sleep: 45s Inactivity", (250, 204, 21)),
        ]

        start_y = 52
        card_height = 40
        spacing = 6

        for idx, (label, val, color) in enumerate(metrics):
            y = start_y + idx * (card_height + spacing)
            draw.rectangle((10, y, lcd.width - 10, y + card_height), fill=(30, 41, 59), outline=(51, 65, 85), width=1)
            draw.text((16, y + 4), label, font=font_label, fill=(148, 163, 184))
            draw.text((16, y + 18), val, font=font_value, fill=color)

        # --- Footer ---
        draw.rectangle((0, 280, lcd.width, lcd.height), fill=(15, 23, 42))
        draw.line([(0, 280), (lcd.width, 280)], fill=(51, 65, 85), width=1)
        draw.text((15, 290), "◀ Press Knob to return to Menu", font=font_hint, fill=(203, 213, 225))

        lcd.render_image(img)

    def handle_knob(self, action: KnobUserAction) -> Optional[str]:
        if action in (KnobUserAction.PRESS, KnobUserAction.TURN_LEFT, KnobUserAction.TURN_RIGHT):
            return "MENU"
        return None
