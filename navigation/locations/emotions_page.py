from PIL import Image, ImageDraw
from ..abstract_location import AbstractLocation
from display.lcd_core import LCDCore
from display.ui_icons import draw_heart_icon, draw_chevron
from state import AppState, KnobUserAction, Mood
from typing import Optional, List, Tuple


class EmotionsPage(AbstractLocation):
    """
    Live Emotional Intensity & Affective Soul Monitor.
    Displays real-time level progress bars for all 11 emotions,
    highlighting the currently dominant/active mood.
    Refreshes every second.
    """

    # Ordered listing of companion emotions with clean labels and distinct accent colors
    EMOTIONS: List[Tuple[Mood, str, Tuple[int, int, int]]] = [
        (Mood.HAPPY, "Happy", (250, 204, 21)),           # Warm Amber/Gold
        (Mood.CURIOUS, "Curious", (192, 132, 252)),      # Vibrant Purple
        (Mood.THINKING, "Thinking", (34, 211, 238)),     # Electric Cyan
        (Mood.LOOKING_AROUND, "Look Around", (52, 211, 153)), # Mint Green
        (Mood.NEUTRAL, "Neutral", (148, 163, 184)),      # Soft Slate
        (Mood.BORED, "Bored", (156, 163, 175)),          # Muted Gray
        (Mood.CONFUSED, "Confused", (251, 146, 60)),     # Sunset Orange
        (Mood.SAD, "Sad", (96, 165, 250)),               # Melancholy Blue
        (Mood.ANGRY, "Angry", (248, 113, 113)),          # Crimson Alert
        (Mood.TOO_COLD, "Too Cold", (59, 130, 246)),     # Frigid Blue
        (Mood.TOO_HOT, "Too Hot", (239, 68, 68)),        # Scorch Red
    ]

    def render(self, lcd: LCDCore, state: AppState) -> None:
        bg_color = (11, 15, 25)  # Obsidian dark
        img = Image.new("RGB", (lcd.width, lcd.height), bg_color)
        draw = ImageDraw.Draw(img)

        font_header = lcd._get_font(size=14, bold=True)
        font_sub = lcd._get_font(size=10, bold=False)
        font_label = lcd._get_font(size=10, bold=False)
        font_label_active = lcd._get_font(size=10, bold=True)
        font_val = lcd._get_font(size=9, bold=False)
        font_val_active = lcd._get_font(size=9, bold=True)
        font_hint = lcd._get_font(size=11, italic=True)

        # --- Header ---
        draw.rectangle((0, 0, lcd.width, 36), fill=(17, 24, 39))
        draw.line([(0, 36), (lcd.width, 36)], fill=(31, 41, 55), width=1)
        draw_heart_icon(draw, 14, 10, size=15, color=(244, 114, 182))
        draw.text((36, 7), "EMOTION ENGINE", font=font_header, fill=(241, 245, 249))
        draw.text((36, 22), "Live emotional intensity & mood", font=font_sub, fill=(107, 114, 128))

        # --- Emotions Level Bars ---
        start_y = 40
        row_h = 18
        spacing = 4

        # Read levels dictionary from state (fallback to 0)
        levels_map = getattr(state, "emotion_levels", {}) or {}

        for idx, (mood, label, accent_color) in enumerate(self.EMOTIONS):
            y = start_y + idx * (row_h + spacing)

            # Check if this emotion is the currently active mood
            is_active = (
                state.mood == mood
                or (isinstance(state.mood, Mood) and state.mood.value == mood.value)
                or (isinstance(state.mood, str) and state.mood == mood.value)
            )

            # Get numeric level (0 - 100)
            raw_level = levels_map.get(mood, levels_map.get(mood.value, 0))
            try:
                level = max(0, min(100, int(raw_level)))
            except (ValueError, TypeError):
                level = 0

            # --- Row Card Background & Active Highlight ---
            if is_active:
                # Active card with glowing outline and highlighted background
                draw.rounded_rectangle(
                    (8, y, lcd.width - 8, y + row_h),
                    radius=4,
                    fill=(30, 41, 59),
                    outline=(56, 189, 248),
                    width=1,
                )
                # Left accent pill
                draw.rounded_rectangle((8, y + 2, 11, y + row_h - 2), radius=1, fill=(56, 189, 248))
                # Active dot indicator
                draw.ellipse((15, y + row_h // 2 - 2, 19, y + row_h // 2 + 2), fill=(56, 189, 248))
            else:
                # Subtle alternating or dark baseline card
                draw.rounded_rectangle(
                    (8, y, lcd.width - 8, y + row_h),
                    radius=4,
                    fill=(15, 20, 31),
                    outline=(23, 32, 48),
                    width=1,
                )

            # --- Label ---
            label_x = 24
            label_font = font_label_active if is_active else font_label
            label_color = (255, 255, 255) if is_active else (156, 163, 175)
            draw.text((label_x, y + 2), label, font=label_font, fill=label_color)

            # --- Progress Bar ---
            bar_x = 100
            bar_w = 90
            bar_y = y + 4
            bar_h = 10

            # Bar track (empty background)
            track_color = (15, 23, 42) if is_active else (23, 30, 43)
            draw.rounded_rectangle(
                (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h),
                radius=3,
                fill=track_color,
                outline=(45, 55, 72) if is_active else (31, 41, 55),
                width=1,
            )

            # Filled bar portion
            fill_w = int(bar_w * (level / 100.0))
            if fill_w > 0:
                if is_active:
                    fill_color = accent_color
                else:
                    # Slightly muted version for non-active emotions
                    fill_color = tuple(max(30, int(c * 0.65)) for c in accent_color)

                fill_right = min(bar_x + bar_w, bar_x + max(4, fill_w))
                draw.rounded_rectangle(
                    (bar_x, bar_y, fill_right, bar_y + bar_h),
                    radius=3,
                    fill=fill_color,
                )

            # --- Value Readout ---
            val_x = 196
            val_text = f"{level:>3}%"
            val_font = font_val_active if is_active else font_val
            val_color = (56, 189, 248) if is_active else (100, 116, 139)
            draw.text((val_x, y + 3), val_text, font=val_font, fill=val_color)

        # --- Footer (Back to Menu Pill) ---
        hint_y = 282
        draw.rounded_rectangle(
            (8, hint_y, lcd.width - 8, hint_y + 32),
            radius=6,
            fill=(23, 37, 84),
            outline=(30, 58, 138),
            width=1,
        )
        draw_chevron(draw, 18, hint_y + 11, size=5, direction="left", color=(147, 197, 253), width=2)
        draw.text((32, hint_y + 8), "Press knob to return to Menu", font=font_hint, fill=(191, 219, 254))

        lcd.render_image(img)

    def handle_knob(self, action: KnobUserAction) -> Optional[str]:
        """Pressing or rotating the knob returns back to Menu."""
        if action in (KnobUserAction.PRESS, KnobUserAction.TURN_LEFT, KnobUserAction.TURN_RIGHT):
            return "MENU"
        return None
