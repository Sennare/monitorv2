from PIL import Image, ImageDraw
from ..abstract_location import AbstractLocation
from display.lcd_core import LCDCore
from display.ui_icons import draw_chart_icon, draw_chevron
from state import AppState, KnobUserAction, StateStore, BoostEmotion, Mood
from typing import Optional


class SensorsPage(AbstractLocation):
    """
    Modern Minimalist Telemetry & Hardware Sensors Monitor.
    Displays live sensor readouts with vector graphics.
    """

    def __init__(self):
        self.state_store = StateStore()

    def on_enter(self) -> None:
        self.state_store.dispatch(BoostEmotion(Mood.CURIOUS, 60))

    def render(self, lcd: LCDCore, state: AppState) -> None:
        bg_color = (11, 15, 25)  # Obsidian dark
        img = Image.new("RGB", (lcd.width, lcd.height), bg_color)
        draw = ImageDraw.Draw(img)

        font_header = lcd._get_font(size=14, bold=True)
        font_sub = lcd._get_font(size=10, bold=False)
        font_label = lcd._get_font(size=10, bold=False)
        font_value = lcd._get_font(size=13, bold=True)
        font_hint = lcd._get_font(size=11, italic=True)

        # --- Header ---
        draw.rectangle((0, 0, lcd.width, 38), fill=(17, 24, 39))
        draw.line([(0, 38), (lcd.width, 38)], fill=(31, 41, 55), width=1)
        draw_chart_icon(draw, 14, 11, size=15, color=(56, 189, 248))
        draw.text((36, 8), "SENSORS & TELEMETRY", font=font_header, fill=(241, 245, 249))
        draw.text((36, 23), "Live hardware diagnostic stream", font=font_sub, fill=(107, 114, 128))

        # Metrics rows
        metrics = [
            ("AMBIENT TEMPERATURE", f"{state.temperature:.2f} °C" if state.temperature else "--.- °C", (251, 191, 36)),
            ("RELATIVE HUMIDITY", f"{state.humidity:.2f} %" if state.humidity else "--.- %", (56, 189, 248)),
            ("PIR PRESENCE", "Motion Active (Present)" if state.someone_around else "No Motion (Standby)", (74, 222, 128) if state.someone_around else (156, 163, 175)),
            ("DATABASE PERSISTENCE", "PostgreSQL (15-min sync)", (192, 132, 252)),
            ("DISPLAY WATCHDOG", "Inactivity Sleep: 45s", (250, 204, 21)),
        ]

        start_y = 48
        card_h = 39
        spacing = 6

        for idx, (label, val, color) in enumerate(metrics):
            y = start_y + idx * (card_h + spacing)
            draw.rounded_rectangle(
                (12, y, lcd.width - 12, y + card_h),
                radius=6,
                fill=(17, 24, 39),
                outline=(31, 41, 55),
                width=1,
            )
            draw.text((20, y + 4), label, font=font_label, fill=(156, 163, 175))
            draw.text((20, y + 18), val, font=font_value, fill=color)

        # --- Footer (Back Button Pill) ---
        hint_y = 276
        draw.rounded_rectangle(
            (12, hint_y, lcd.width - 12, hint_y + 34),
            radius=6,
            fill=(23, 37, 84),
            outline=(30, 58, 138),
            width=1,
        )
        draw_chevron(draw, 22, hint_y + 12, size=5, direction="left", color=(147, 197, 253), width=2)
        draw.text((36, hint_y + 9), "Press knob to return to Menu", font=font_hint, fill=(191, 219, 254))

        lcd.render_image(img)

    def handle_knob(self, action: KnobUserAction) -> Optional[str]:
        if action in (KnobUserAction.PRESS, KnobUserAction.TURN_LEFT, KnobUserAction.TURN_RIGHT):
            return "MENU"
        return None
