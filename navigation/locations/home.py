from PIL import Image, ImageDraw
from ..abstract_location import AbstractLocation
from display.lcd_core import LCDCore
from state import AppState, KnobUserAction
from typing import Optional


class Home(AbstractLocation):
    """
    Main Status Dashboard showing real-time environmental metrics,
    presence status, and affective mood.
    """

    def render(self, lcd: LCDCore, state: AppState) -> None:
        img = Image.new("RGB", (lcd.width, lcd.height), (15, 23, 42))  # Slate dark background
        draw = ImageDraw.Draw(img)

        font_title = lcd._get_font(size=16, bold=True)
        font_large = lcd._get_font(size=22, bold=True)
        font_label = lcd._get_font(size=11, bold=False)
        font_hint = lcd._get_font(size=12, italic=True)

        # --- Top Header ---
        draw.rectangle((0, 0, lcd.width, 38), fill=(30, 41, 59))
        draw.text((15, 10), "REMOTE MONITOR", font=font_title, fill=(56, 189, 248))
        draw.line([(0, 38), (lcd.width, 38)], fill=(71, 85, 105), width=2)

        # --- Temperature & Humidity Card ---
        # Card background
        draw.rectangle((12, 48, lcd.width - 12, 140), fill=(30, 41, 59), outline=(51, 65, 85), width=1)
        
        # Temp column
        draw.text((24, 56), "TEMPERATURE", font=font_label, fill=(148, 163, 184))
        temp_str = f"{state.temperature:.1f} °C" if state.temperature else "--.- °C"
        draw.text((24, 76), temp_str, font=font_large, fill=(251, 146, 60))  # Warm orange

        # Divider line
        draw.line([(lcd.width // 2, 54), (lcd.width // 2, 134)], fill=(51, 65, 85), width=1)

        # Humidity column
        draw.text((lcd.width // 2 + 12, 56), "HUMIDITY", font=font_label, fill=(148, 163, 184))
        humi_str = f"{state.humidity:.1f} %" if state.humidity else "--.- %"
        draw.text((lcd.width // 2 + 12, 76), humi_str, font=font_large, fill=(56, 189, 248))  # Cyan

        # --- Presence Status Card ---
        draw.rectangle((12, 148, lcd.width - 12, 202), fill=(30, 41, 59), outline=(51, 65, 85), width=1)
        draw.text((24, 156), "PHYSICAL PRESENCE", font=font_label, fill=(148, 163, 184))
        
        # Status indicator circle
        dot_color = (74, 222, 128) if state.someone_around else (100, 116, 139)  # Green / Gray
        pres_text = "Someone Present" if state.someone_around else "Standby (Idle)"
        draw.ellipse((24, 178, 34, 188), fill=dot_color)
        draw.text((42, 174), pres_text, font=font_title, fill=(241, 245, 249))

        # --- Soul / Mood Card ---
        draw.rectangle((12, 210, lcd.width - 12, 264), fill=(30, 41, 59), outline=(51, 65, 85), width=1)
        draw.text((24, 218), "ACTIVE MOOD", font=font_label, fill=(148, 163, 184))
        mood_name = state.mood.value.upper()
        draw.text((24, 234), f"♥ {mood_name}", font=font_title, fill=(244, 114, 182))  # Rose / pink

        # --- Footer Hint ---
        draw.rectangle((0, 276, lcd.width, lcd.height), fill=(15, 23, 42))
        draw.line([(0, 276), (lcd.width, 276)], fill=(51, 65, 85), width=1)
        draw.text((20, 286), "● Press knob for Menu", font=font_hint, fill=(203, 213, 225))
        draw.text((20, 302), "Auto-sleep after 45s inactivity", font=font_label, fill=(100, 116, 139))

        lcd.render_image(img)

    def handle_knob(self, action: KnobUserAction) -> Optional[str]:
        # Clicking or turning opens the menu
        if action in (KnobUserAction.PRESS, KnobUserAction.TURN_RIGHT, KnobUserAction.TURN_LEFT):
            return "MENU"
        return None