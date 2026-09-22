from PIL import Image, ImageDraw
from ..abstract_location import AbstractLocation
from display.lcd_core import LCDCore
from display.ui_icons import draw_warning_icon, draw_chevron
from state import AppState, KnobUserAction, StateStore, BoostEmotion, Mood
from typing import Optional


class Settings(AbstractLocation):
    """
    Modern Minimalist Settings Screen.
    Entering angers the companion ("doesn't want to be adjusted!"),
    immediately triggering the ANGRY emotion and expression on the OLED display.
    """

    ITEMS = [
        ("Personality Profile", "DENIED"),
        ("Inactivity Sleep: 45s", "FIXED"),
        ("Mood Sensitivity: High", "LOCKED"),
        ("Back to Menu", "BACK"),
    ]

    def __init__(self):
        self.state_store = StateStore()
        self.selected_index = len(self.ITEMS) - 1  # Default to Back for safety
        self.alert_message: Optional[str] = None

    def on_enter(self) -> None:
        # Crucial emotional connection: trigger ANGRY emotion on entry!
        print("[settings] User accessed Settings! Dispensing ANGRY emotion to soul.")
        self.state_store.dispatch(BoostEmotion(Mood.ANGRY, 100))
        self.alert_message = "HEY! Don't touch me! >:("

    def render(self, lcd: LCDCore, state: AppState) -> None:
        bg_color = (20, 10, 14)  # Obsidian crimson dark
        img = Image.new("RGB", (lcd.width, lcd.height), bg_color)
        draw = ImageDraw.Draw(img)

        font_header = lcd._get_font(size=14, bold=True)
        font_sub = lcd._get_font(size=10, bold=False)
        font_warn = lcd._get_font(size=12, bold=True)
        font_item = lcd._get_font(size=12, bold=True)
        font_status = lcd._get_font(size=10, bold=False)
        font_hint = lcd._get_font(size=11, italic=True)

        # --- Header ---
        draw.rectangle((0, 0, lcd.width, 38), fill=(127, 29, 29))
        draw.line([(0, 38), (lcd.width, 38)], fill=(185, 28, 28), width=1)
        draw_warning_icon(draw, 14, 11, size=16, color=(254, 202, 202))
        draw.text((36, 8), "SYSTEM SETTINGS", font=font_header, fill=(254, 226, 226))
        draw.text((36, 23), "Protected appliance parameters", font=font_sub, fill=(252, 165, 165))

        # --- Angry Reaction Banner ---
        banner_text = self.alert_message or "System resists modification!"
        draw.rounded_rectangle(
            (12, 46, lcd.width - 12, 82),
            radius=6,
            fill=(153, 27, 27),
            outline=(239, 68, 68),
            width=1,
        )
        draw.text((20, 50), "REACTION:", font=font_sub, fill=(254, 202, 202))
        draw.text((20, 63), banner_text, font=font_warn, fill=(254, 240, 138))

        # --- Settings Items ---
        start_y = 92
        card_h = 40
        spacing = 7

        for idx, (label, value) in enumerate(self.ITEMS):
            y = start_y + idx * (card_h + spacing)
            is_selected = idx == self.selected_index
            is_back = value == "BACK"

            if is_selected:
                card_bg = (153, 27, 27) if not is_back else (30, 41, 59)
                card_outline = (248, 113, 113) if not is_back else (96, 165, 250)
                text_color = (255, 255, 255)
                val_color = (254, 240, 138) if not is_back else (147, 197, 253)
            else:
                card_bg = (45, 12, 18) if not is_back else (17, 24, 39)
                card_outline = (88, 20, 30) if not is_back else (31, 41, 55)
                text_color = (248, 113, 113) if not is_back else (156, 163, 175)
                val_color = (185, 28, 28) if not is_back else (107, 114, 128)

            draw.rounded_rectangle(
                (12, y, lcd.width - 12, y + card_h),
                radius=6,
                fill=card_bg,
                outline=card_outline,
                width=1 if not is_selected else 2,
            )

            # Left accent pill for selected item
            if is_selected:
                accent_color = (248, 113, 113) if not is_back else (96, 165, 250)
                draw.rounded_rectangle((12, y + 6, 16, y + card_h - 6), radius=2, fill=accent_color)

            if is_back:
                draw_chevron(draw, 22, y + 15, size=5, direction="left", color=text_color, width=2)
                draw.text((36, y + 13), label, font=font_item, fill=text_color)
            else:
                draw.text((22, y + 7), label, font=font_item, fill=text_color)
                draw.text((22, y + 23), f"[{value}]", font=font_status, fill=val_color)

        # --- Footer Pill ---
        hint_y = 276
        draw.rounded_rectangle(
            (12, hint_y, lcd.width - 12, hint_y + 34),
            radius=6,
            fill=(45, 12, 18),
            outline=(88, 20, 30),
            width=1,
        )
        draw.text((20, hint_y + 9), "Rotate: Select   •   Press: Trigger", font=font_hint, fill=(252, 165, 165))

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
