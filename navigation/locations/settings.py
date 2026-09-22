from PIL import Image, ImageDraw
from ..abstract_location import AbstractLocation
from display.lcd_core import LCDCore
from state import AppState, KnobUserAction, StateStore, BoostEmotion, Mood
from typing import Optional


class Settings(AbstractLocation):
    """
    Settings Location:
    Entering this screen angers the appliance ("the thing doesn't want to be adjusted!"),
    immediately triggering the ANGRY emotion and facial expression on the OLED display!
    """

    ITEMS = [
        ("• Personality Recalibration", "DENIED"),
        ("• Inactivity Timeout: 45s", "FIXED"),
        ("• Mood Bias: Grumpy", "LOCKED"),
        ("◀ Back to Menu", "BACK"),
    ]

    def __init__(self):
        self.state_store = StateStore()
        self.selected_index = len(self.ITEMS) - 1  # Default to "Back" for safety
        self.alert_message: Optional[str] = None

    def on_enter(self) -> None:
        # Crucial emotional connection: trigger ANGRY emotion on entry!
        print("[settings] User accessed Settings! Dispensing ANGRY emotion to soul.")
        self.state_store.dispatch(BoostEmotion(Mood.ANGRY, 100))
        self.alert_message = "HEY! Don't touch me! >:("

    def render(self, lcd: LCDCore, state: AppState) -> None:
        img = Image.new("RGB", (lcd.width, lcd.height), (24, 12, 16))  # Deep crimson dark background
        draw = ImageDraw.Draw(img)

        font_title = lcd._get_font(size=16, bold=True)
        font_warn = lcd._get_font(size=13, bold=True)
        font_item = lcd._get_font(size=13, bold=False)
        font_hint = lcd._get_font(size=11, italic=True)

        # --- Header ---
        draw.rectangle((0, 0, lcd.width, 42), fill=(127, 29, 29))  # Dark red
        draw.text((15, 12), "⚠️ SYSTEM SETTINGS", font=font_title, fill=(254, 202, 202))
        draw.line([(0, 42), (lcd.width, 42)], fill=(185, 28, 28), width=2)

        # --- Angry Alert Banner ---
        banner_text = self.alert_message or "System does not want changes!"
        draw.rectangle((10, 50, lcd.width - 10, 86), fill=(153, 27, 27), outline=(239, 68, 68), width=1)
        draw.text((18, 54), "REACTION:", font=font_hint, fill=(254, 226, 226))
        draw.text((18, 68), banner_text, font=font_warn, fill=(254, 240, 138))

        # --- Settings Items ---
        start_y = 96
        item_height = 38
        spacing = 8

        for idx, (label, value) in enumerate(self.ITEMS):
            y = start_y + idx * (item_height + spacing)
            is_selected = idx == self.selected_index

            if is_selected:
                draw.rectangle(
                    (10, y, lcd.width - 10, y + item_height),
                    fill=(185, 28, 28),
                    outline=(252, 165, 165),
                    width=2,
                )
                text_color = (255, 255, 255)
                draw.text((16, y + 10), f"▶ {label}", font=font_item, fill=text_color)
            else:
                draw.rectangle(
                    (10, y, lcd.width - 10, y + item_height),
                    fill=(69, 10, 10),
                    outline=(127, 29, 29),
                    width=1,
                )
                text_color = (254, 202, 202)
                draw.text((20, y + 10), label, font=font_item, fill=text_color)

        # --- Footer Hint ---
        draw.rectangle((0, 280, lcd.width, lcd.height), fill=(24, 12, 16))
        draw.line([(0, 280), (lcd.width, 280)], fill=(127, 29, 29), width=1)
        draw.text((15, 290), "Turn: Select   •   Click: Interact", font=font_hint, fill=(252, 165, 165))

        lcd.render_image(img)

    def handle_knob(self, action: KnobUserAction) -> Optional[str]:
        if action == KnobUserAction.TURN_RIGHT:
            self.selected_index = (self.selected_index + 1) % len(self.ITEMS)
            return None
        elif action == KnobUserAction.TURN_LEFT:
            self.selected_index = (self.selected_index - 1) % len(self.ITEMS)
            return None
        elif action == KnobUserAction.PRESS:
            action_code = self.ITEMS[self.selected_index][1]
            if action_code == "BACK":
                return "MENU"
            else:
                # User poked a forbidden setting: re-trigger angry reaction!
                self.alert_message = "STOP POKING ME! >:("
                self.state_store.dispatch(BoostEmotion(Mood.ANGRY, 100))
                return None
        return None
