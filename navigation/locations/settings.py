from PIL import Image, ImageDraw
from ..abstract_location import AbstractLocation
from display.lcd_core import LCDCore
from display.ui_icons import draw_warning_icon, draw_chevron
from state import AppState, KnobUserAction, StateStore, BoostEmotion, Mood
from typing import Optional, List, Tuple


class Settings(AbstractLocation):
    """
    Modern Minimalist Settings Screen.
    Includes user-adjustable backlight brightness (10% to 100%).
    Entering angers the companion ("doesn't want to be adjusted!"),
    immediately triggering the ANGRY emotion and expression on the OLED display.
    """

    def __init__(self):
        self.state_store = StateStore()
        self.lcd = LCDCore()
        self.selected_index: int = 1  # Default to Backlight Brightness for immediate usability
        self.alert_message: Optional[str] = None
        self.is_editing_brightness: bool = False

    def _get_items(self) -> List[Tuple[str, str]]:
        brightness_val = f"{self.lcd.get_brightness()}%"
        if self.is_editing_brightness:
            brightness_val = f"< {self.lcd.get_brightness()}% >"

        return [
            ("Personality Profile", "DENIED"),
            ("Backlight Brightness", brightness_val),
            ("Inactivity Sleep: 45s", "FIXED"),
            ("Mood Sensitivity: High", "LOCKED"),
            ("Back to Menu", "BACK"),
        ]

    def on_enter(self) -> None:
        # Crucial emotional connection: trigger ANGRY emotion on entry!
        print("[settings] User accessed Settings! Dispensing ANGRY emotion to soul.")
        try:
            self.state_store.dispatch(BoostEmotion(Mood.ANGRY, 100))
        except Exception as e:
            print(f"[settings] BoostEmotion error: {e}")
        self.alert_message = "HEY! Don't touch me! >:("
        self.is_editing_brightness = False

    def render(self, lcd: LCDCore, state: AppState) -> None:
        try:
            self._render_content(lcd, state)
        except Exception as e:
            import traceback
            print(f"[settings] Error during Settings.render: {e}")
            traceback.print_exc()

    def _render_content(self, lcd: LCDCore, state: AppState) -> None:
        bg_color = (20, 10, 14)  # Obsidian crimson dark
        img = Image.new("RGB", (lcd.width, lcd.height), bg_color)
        draw = ImageDraw.Draw(img)

        font_header = lcd._get_font(size=14, bold=True)
        font_sub = lcd._get_font(size=9, bold=False)
        font_warn = lcd._get_font(size=11, bold=True)
        font_item = lcd._get_font(size=11, bold=True)
        font_status = lcd._get_font(size=10, bold=False)
        font_hint = lcd._get_font(size=10, italic=True)

        # --- Header ---
        draw.rectangle((0, 0, lcd.width, 36), fill=(127, 29, 29))
        draw.line([(0, 36), (lcd.width, 36)], fill=(185, 28, 28), width=1)
        draw_warning_icon(draw, 14, 10, size=16, color=(254, 202, 202))
        draw.text((36, 7), "SYSTEM SETTINGS", font=font_header, fill=(254, 226, 226))
        draw.text((36, 22), "Protected appliance parameters", font=font_sub, fill=(252, 165, 165))

        # --- Reaction Banner ---
        banner_text = self.alert_message or "System resists modification!"
        draw.rounded_rectangle(
            (12, 42, lcd.width - 12, 74),
            radius=6,
            fill=(153, 27, 27),
            outline=(239, 68, 68),
            width=1,
        )
        draw.text((20, 46), "REACTION:", font=font_sub, fill=(254, 202, 202))
        draw.text((20, 58), banner_text, font=font_warn, fill=(254, 240, 138))

        # --- Settings Items ---
        items = self._get_items()
        start_y = 80
        card_h = 34
        spacing = 5

        for idx, (label, value) in enumerate(items):
            y = start_y + idx * (card_h + spacing)
            is_selected = idx == self.selected_index
            is_back = (idx == len(items) - 1)
            is_bright = (idx == 1)

            if is_selected:
                if self.is_editing_brightness and is_bright:
                    # Glowing edit mode style
                    card_bg = (69, 26, 3)
                    card_outline = (251, 191, 36)
                    text_color = (254, 240, 138)
                    val_color = (251, 191, 36)
                elif is_back:
                    card_bg = (30, 41, 59)
                    card_outline = (96, 165, 250)
                    text_color = (255, 255, 255)
                    val_color = (147, 197, 253)
                elif is_bright:
                    card_bg = (45, 20, 10)
                    card_outline = (245, 158, 11)
                    text_color = (255, 255, 255)
                    val_color = (251, 191, 36)
                else:
                    card_bg = (153, 27, 27)
                    card_outline = (248, 113, 113)
                    text_color = (255, 255, 255)
                    val_color = (254, 240, 138)
            else:
                if is_back:
                    card_bg = (17, 24, 39)
                    card_outline = (31, 41, 55)
                    text_color = (156, 163, 175)
                    val_color = (107, 114, 128)
                elif is_bright:
                    card_bg = (30, 15, 10)
                    card_outline = (80, 40, 15)
                    text_color = (251, 191, 36)
                    val_color = (217, 119, 6)
                else:
                    card_bg = (45, 12, 18)
                    card_outline = (88, 20, 30)
                    text_color = (248, 113, 113)
                    val_color = (185, 28, 28)

            draw.rounded_rectangle(
                (12, y, lcd.width - 12, y + card_h),
                radius=6,
                fill=card_bg,
                outline=card_outline,
                width=2 if is_selected else 1,
            )

            # Left accent pill for selected item
            if is_selected:
                accent_color = (251, 191, 36) if (is_bright and self.is_editing_brightness) else (
                    (96, 165, 250) if is_back else (248, 113, 113)
                )
                draw.rounded_rectangle((12, y + 4, 16, y + card_h - 4), radius=2, fill=accent_color)

            if is_back:
                draw_chevron(draw, 22, y + 12, size=5, direction="left", color=text_color, width=2)
                draw.text((36, y + 10), label, font=font_item, fill=text_color)
            else:
                draw.text((22, y + 5), label, font=font_item, fill=text_color)
                draw.text((22, y + 18), f"[{value}]", font=font_status, fill=val_color)

        # --- Footer Pill ---
        hint_y = 278
        draw.rounded_rectangle(
            (12, hint_y, lcd.width - 12, hint_y + 32),
            radius=6,
            fill=(45, 12, 18),
            outline=(88, 20, 30),
            width=1,
        )
        if self.is_editing_brightness:
            draw.text((20, hint_y + 8), "Turn: < Brightness >   |   Press: Save", font=font_hint, fill=(254, 240, 138))
        else:
            draw.text((20, hint_y + 8), "Rotate: Select   |   Press: Edit / Action", font=font_hint, fill=(252, 165, 165))

        lcd.render_image(img)

    def handle_knob(self, action: KnobUserAction) -> Optional[str]:
        items = self._get_items()

        # Handle active brightness editing mode
        if self.is_editing_brightness:
            if action == KnobUserAction.TURN_RIGHT:
                new_val = min(100, self.lcd.get_brightness() + 10)
                self.lcd.set_brightness(new_val)
                if new_val >= 90:
                    self.alert_message = "Blinding! My eyes! >:("
                else:
                    self.alert_message = f"Brightness set to {new_val}%"
                return None
            elif action == KnobUserAction.TURN_LEFT:
                new_val = max(10, self.lcd.get_brightness() - 10)
                self.lcd.set_brightness(new_val)
                if new_val <= 30:
                    self.alert_message = "Hey! It's too dark! >:("
                else:
                    self.alert_message = f"Brightness set to {new_val}%"
                return None
            elif action == KnobUserAction.PRESS:
                self.is_editing_brightness = False
                self.alert_message = f"Brightness saved at {self.lcd.get_brightness()}%!"
                return None
            return None

        # Standard navigation mode
        if action == KnobUserAction.TURN_RIGHT:
            self.selected_index = (self.selected_index + 1) % len(items)
            return None
        elif action == KnobUserAction.TURN_LEFT:
            self.selected_index = (self.selected_index - 1) % len(items)
            return None
        elif action == KnobUserAction.PRESS:
            if self.selected_index == 1:
                # Enter brightness edit mode
                self.is_editing_brightness = True
                self.alert_message = "Turn knob to adjust, click to save"
                return None
            elif self.selected_index == len(items) - 1:
                # Back to Menu
                return "MENU"
            else:
                # Forbidden item clicked
                self.alert_message = "STOP POKING ME! >:("
                self.state_store.dispatch(BoostEmotion(Mood.ANGRY, 100))
                return None
        return None
