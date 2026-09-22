from PIL import Image, ImageDraw
from ..abstract_location import AbstractLocation
from display.lcd_core import LCDCore
from display.ui_icons import (
    draw_temp_icon,
    draw_humidity_icon,
    draw_presence_radar,
    draw_heart_icon,
    draw_chevron,
)
from state import AppState, KnobUserAction
from typing import Optional


class Home(AbstractLocation):
    """
    Modern Minimalist Status Dashboard.
    Displays real-time ambient metrics, presence detection, and affective soul mood
    with crisp vector iconography.
    """

    def render(self, lcd: LCDCore, state: AppState) -> None:
        bg_color = (11, 15, 25)  # Deep luxury obsidian blue
        img = Image.new("RGB", (lcd.width, lcd.height), bg_color)
        draw = ImageDraw.Draw(img)

        font_header = lcd._get_font(size=14, bold=True)
        font_pill = lcd._get_font(size=10, bold=True)
        font_large = lcd._get_font(size=22, bold=True)
        font_card_title = lcd._get_font(size=11, bold=True)
        font_subtext = lcd._get_font(size=10, bold=False)
        font_hint = lcd._get_font(size=11, italic=True)

        # ==========================================
        # 1. Header Bar
        # ==========================================
        draw.rectangle((0, 0, lcd.width, 36), fill=(17, 24, 39))
        draw.line([(0, 36), (lcd.width, 36)], fill=(31, 41, 55), width=1)

        # Title
        draw.text((14, 10), "REMOTE MONITOR", font=font_header, fill=(241, 245, 249))

        # "LIVE" pill tag in top-right
        pill_x = lcd.width - 52
        draw.rounded_rectangle((pill_x, 8, pill_x + 40, 24), radius=4, fill=(19, 78, 74))
        draw.ellipse((pill_x + 6, 14, pill_x + 10, 18), fill=(52, 211, 153))
        draw.text((pill_x + 14, 10), "LIVE", font=font_pill, fill=(167, 243, 208))

        # ==========================================
        # 2. Environmental Metrics Cards (Side-by-Side)
        # ==========================================
        card_w = (lcd.width - 32) // 2
        card_y = 46
        card_h = 76

        # --- Temperature Card (Left) ---
        x_temp = 12
        draw.rounded_rectangle(
            (x_temp, card_y, x_temp + card_w, card_y + card_h),
            radius=8,
            fill=(17, 24, 39),
            outline=(31, 41, 55),
            width=1,
        )
        draw_temp_icon(draw, x_temp + 10, card_y + 10, size=14, color=(251, 146, 60))
        draw.text((x_temp + 30, card_y + 10), "TEMP", font=font_card_title, fill=(156, 163, 175))

        temp_str = f"{state.temperature:.1f}°" if state.temperature else "--.-°"
        draw.text((x_temp + 10, card_y + 30), temp_str, font=font_large, fill=(251, 191, 36))
        draw.text((x_temp + 10, card_y + 56), "CELSIUS", font=font_subtext, fill=(107, 114, 128))

        # --- Humidity Card (Right) ---
        x_humi = x_temp + card_w + 8
        draw.rounded_rectangle(
            (x_humi, card_y, x_humi + card_w, card_y + card_h),
            radius=8,
            fill=(17, 24, 39),
            outline=(31, 41, 55),
            width=1,
        )
        draw_humidity_icon(draw, x_humi + 10, card_y + 10, size=14, color=(56, 189, 248))
        draw.text((x_humi + 30, card_y + 10), "HUMIDITY", font=font_card_title, fill=(156, 163, 175))

        humi_str = f"{state.humidity:.0f}%" if state.humidity else "--%"
        draw.text((x_humi + 10, card_y + 30), humi_str, font=font_large, fill=(56, 189, 248))
        draw.text((x_humi + 10, card_y + 56), "RELATIVE", font=font_subtext, fill=(107, 114, 128))

        # ==========================================
        # 3. Physical Presence Card
        # ==========================================
        pres_y = 132
        pres_h = 58
        draw.rounded_rectangle(
            (12, pres_y, lcd.width - 12, pres_y + pres_h),
            radius=8,
            fill=(17, 24, 39),
            outline=(31, 41, 55),
            width=1,
        )
        draw_presence_radar(draw, 22, pres_y + 18, size=20, active=state.someone_around)

        pres_title = "PRESENCE DETECTED" if state.someone_around else "ROOM EMPTY (STANDBY)"
        title_color = (74, 222, 128) if state.someone_around else (209, 213, 219)
        draw.text((52, pres_y + 13), pres_title, font=font_card_title, fill=title_color)

        pres_sub = "PIR sensor: motion active" if state.someone_around else "Inactivity sleep: 60s timer"
        draw.text((52, pres_y + 31), pres_sub, font=font_subtext, fill=(107, 114, 128))

        # ==========================================
        # 4. Affective Soul / Mood Card
        # ==========================================
        mood_y = 200
        mood_h = 58
        draw.rounded_rectangle(
            (12, mood_y, lcd.width - 12, mood_y + mood_h),
            radius=8,
            fill=(17, 24, 39),
            outline=(31, 41, 55),
            width=1,
        )
        draw_heart_icon(draw, 22, mood_y + 20, size=18, color=(244, 114, 182))

        draw.text((52, mood_y + 13), "COMPANION EMOTION", font=font_card_title, fill=(156, 163, 175))
        mood_text = state.mood.value.upper()
        draw.text((52, mood_y + 31), mood_text, font=font_card_title, fill=(244, 114, 182))

        # ==========================================
        # 5. Bottom Navigation Hint (Pill Button)
        # ==========================================
        hint_y = 274
        hint_h = 36
        draw.rounded_rectangle(
            (12, hint_y, lcd.width - 12, hint_y + hint_h),
            radius=8,
            fill=(23, 37, 84),  # Soft navy
            outline=(30, 58, 138),
            width=1,
        )
        draw.text((26, hint_y + 10), "Press knob for Menu", font=font_hint, fill=(191, 219, 254))
        draw_chevron(draw, lcd.width - 32, hint_y + 12, size=6, direction="right", color=(147, 197, 253))

        lcd.render_image(img)

    def handle_knob(self, action: KnobUserAction) -> Optional[str]:
        if action in (KnobUserAction.PRESS, KnobUserAction.TURN_RIGHT, KnobUserAction.TURN_LEFT):
            return "MENU"
        return None