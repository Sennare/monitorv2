from PIL import Image, ImageDraw
from ..abstract_location import AbstractLocation
from display.lcd_core import LCDCore
from display.ui_icons import (
    draw_home_icon,
    draw_chart_icon,
    draw_settings_icon,
    draw_chevron,
)
from state import AppState, KnobUserAction
from typing import Optional


class Menu(AbstractLocation):
    """
    Modern Minimalist Menu.
    Uses clean vector icons and rounded selection cards.
    """

    ITEMS = [
        ("Homepage", "HOME", draw_home_icon),
        ("Sensors Info", "SENSORS", draw_chart_icon),
        ("Settings", "SETTINGS", draw_settings_icon),
    ]

    def __init__(self):
        self.selected_index = 0

    def render(self, lcd: LCDCore, state: AppState) -> None:
        bg_color = (11, 15, 25)  # Obsidian dark
        img = Image.new("RGB", (lcd.width, lcd.height), bg_color)
        draw = ImageDraw.Draw(img)

        font_header = lcd._get_font(size=14, bold=True)
        font_sub = lcd._get_font(size=10, bold=False)
        font_item = lcd._get_font(size=13, bold=True)
        font_hint = lcd._get_font(size=11, italic=True)

        # --- Header ---
        draw.rectangle((0, 0, lcd.width, 38), fill=(17, 24, 39))
        draw.line([(0, 38), (lcd.width, 38)], fill=(31, 41, 55), width=1)
        draw.text((14, 8), "MAIN NAVIGATION", font=font_header, fill=(241, 245, 249))
        draw.text((14, 23), "Select a screen location", font=font_sub, fill=(107, 114, 128))

        # --- Menu Cards ---
        start_y = 52
        card_h = 46
        spacing = 10

        for idx, (label, _, icon_fn) in enumerate(self.ITEMS):
            y = start_y + idx * (card_h + spacing)
            is_selected = idx == self.selected_index

            if is_selected:
                # Active card with electric cyan/blue accent
                card_bg = (30, 41, 59)
                card_outline = (56, 189, 248)
                text_color = (255, 255, 255)
                icon_color = (56, 189, 248)
                badge_bg = (15, 23, 42)
            else:
                card_bg = (17, 24, 39)
                card_outline = (31, 41, 55)
                text_color = (156, 163, 175)
                icon_color = (100, 116, 139)
                badge_bg = (11, 15, 25)

            # Card rounded rectangle
            draw.rounded_rectangle(
                (12, y, lcd.width - 12, y + card_h),
                radius=8,
                fill=card_bg,
                outline=card_outline,
                width=1 if not is_selected else 2,
            )

            # Left accent pill for selected card
            if is_selected:
                draw.rounded_rectangle((12, y + 6, 16, y + card_h - 6), radius=2, fill=(56, 189, 248))

            # Icon badge box
            draw.rounded_rectangle(
                (24, y + 9, 52, y + card_h - 9),
                radius=6,
                fill=badge_bg,
            )
            icon_fn(draw, 30, y + 15, size=16, color=icon_color)

            # Text label
            draw.text((64, y + 14), label, font=font_item, fill=text_color)

            # Right chevron arrow
            chevron_color = (56, 189, 248) if is_selected else (55, 65, 81)
            draw_chevron(draw, lcd.width - 26, y + 18, size=5, direction="right", color=chevron_color, width=2)

        # --- Footer Pill ---
        hint_y = 276
        draw.rounded_rectangle(
            (12, hint_y, lcd.width - 12, hint_y + 34),
            radius=6,
            fill=(17, 24, 39),
            outline=(31, 41, 55),
            width=1,
        )
        draw.text((20, hint_y + 9), "Rotate: Browse   •   Press: Open", font=font_hint, fill=(156, 163, 175))

        lcd.render_image(img)

    def handle_knob(self, action: KnobUserAction) -> Optional[str]:
        if action == KnobUserAction.TURN_RIGHT:
            self.selected_index = (self.selected_index + 1) % len(self.ITEMS)
            return None
        elif action == KnobUserAction.TURN_LEFT:
            self.selected_index = (self.selected_index - 1) % len(self.ITEMS)
            return None
        elif action == KnobUserAction.PRESS:
            return self.ITEMS[self.selected_index][1]
        return None