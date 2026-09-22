from PIL import Image, ImageDraw
from ..abstract_location import AbstractLocation
from display.lcd_core import LCDCore
from state import AppState, KnobUserAction
from typing import Optional


class Menu(AbstractLocation):
    """
    Main Navigation Menu.
    Allows user to select between Home, Sensors, Settings, and Mascot using the rotary knob.
    """

    ITEMS = [
        ("🏠  Homepage", "HOME"),
        ("📊  Sensors Info", "SENSORS"),
        ("⚙️  Settings", "SETTINGS"),
        ("🐱  Cat Mascot", "CAT"),
    ]

    def __init__(self):
        self.selected_index = 0

    def render(self, lcd: LCDCore, state: AppState) -> None:
        img = Image.new("RGB", (lcd.width, lcd.height), (15, 23, 42))  # Dark slate
        draw = ImageDraw.Draw(img)

        font_title = lcd._get_font(size=16, bold=True)
        font_item = lcd._get_font(size=15, bold=False)
        font_hint = lcd._get_font(size=11, italic=True)

        # --- Header ---
        draw.rectangle((0, 0, lcd.width, 42), fill=(30, 41, 59))
        draw.text((15, 12), "☰ MAIN MENU", font=font_title, fill=(56, 189, 248))
        draw.line([(0, 42), (lcd.width, 42)], fill=(71, 85, 105), width=2)

        # --- Menu Items ---
        start_y = 60
        item_height = 46
        spacing = 10

        for idx, (label, _) in enumerate(self.ITEMS):
            y = start_y + idx * (item_height + spacing)
            is_selected = idx == self.selected_index

            if is_selected:
                # Highlighted card with bright border
                draw.rectangle(
                    (12, y, lcd.width - 12, y + item_height),
                    fill=(37, 99, 235),  # Royal blue highlight
                    outline=(147, 197, 253),
                    width=2,
                )
                text_color = (255, 255, 255)
                # Cursor arrow
                draw.text((20, y + 12), f"▶  {label}", font=font_item, fill=text_color)
            else:
                # Normal card
                draw.rectangle(
                    (12, y, lcd.width - 12, y + item_height),
                    fill=(30, 41, 59),
                    outline=(51, 65, 85),
                    width=1,
                )
                text_color = (203, 213, 225)
                draw.text((26, y + 12), label, font=font_item, fill=text_color)

        # --- Footer Hint ---
        draw.rectangle((0, 280, lcd.width, lcd.height), fill=(15, 23, 42))
        draw.line([(0, 280), (lcd.width, 280)], fill=(51, 65, 85), width=1)
        draw.text((15, 290), "Turn: Navigate   •   Click: Open", font=font_hint, fill=(148, 163, 184))

        lcd.render_image(img)

    def handle_knob(self, action: KnobUserAction) -> Optional[str]:
        if action == KnobUserAction.TURN_RIGHT:
            self.selected_index = (self.selected_index + 1) % len(self.ITEMS)
            return None  # Re-renders current page
        elif action == KnobUserAction.TURN_LEFT:
            self.selected_index = (self.selected_index - 1) % len(self.ITEMS)
            return None  # Re-renders current page
        elif action == KnobUserAction.PRESS:
            return self.ITEMS[self.selected_index][1]
        return None