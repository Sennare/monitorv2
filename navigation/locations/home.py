import math
from typing import Optional, Any, Tuple
from PIL import Image, ImageDraw

from ..abstract_location import AbstractLocation
from display.lcd_core import LCDCore
from display.ui_icons import draw_chevron
from state import AppState, KnobUserAction


def get_temp_color(temp: Optional[float]) -> Tuple[int, int, int]:
    """
    Interpolates color from deep blue (cold) -> green/yellow (mild) -> orange/red (hot).
    """
    if temp is None or temp <= 0:
        return (59, 130, 246)  # Default cold blue

    stops = [
        (10.0, (59, 130, 246)),  # Blue (Cold)
        (16.0, (6, 182, 212)),   # Cyan
        (20.0, (34, 197, 94)),   # Green (Comfort/Eco)
        (24.0, (234, 179, 8)),   # Yellow
        (28.0, (249, 115, 22)),  # Orange
        (34.0, (239, 68, 68)),   # Red (Hot)
    ]

    if temp <= stops[0][0]:
        return stops[0][1]
    if temp >= stops[-1][0]:
        return stops[-1][1]

    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t0 <= temp <= t1:
            ratio = (temp - t0) / (t1 - t0)
            r = int(c0[0] + ratio * (c1[0] - c0[0]))
            g = int(c0[1] + ratio * (c1[1] - c0[1]))
            b = int(c0[2] + ratio * (c1[2] - c0[2]))
            return (r, g, b)
    return stops[-1][1]


def draw_gauge_arc(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    r: int,
    w: int,
    start_angle: float,
    end_angle: float,
    ratio: float,
    track_color: Tuple[int, int, int],
    active_color: Tuple[int, int, int],
) -> None:
    """
    Draws a circular gauge arc with rounded track end-caps and an illuminated tip knob.
    Coordinates are calculated so the stroke centerline aligns precisely at radius `r`.
    """
    half_w = w / 2.0
    bbox = [cx - r - half_w, cy - r - half_w, cx + r + half_w, cy + r + half_w]
    total_span = end_angle - start_angle

    # 1. Background recessed track
    draw.arc(bbox, start=start_angle, end=end_angle, fill=track_color, width=w)

    rad_start = math.radians(start_angle)
    rad_end = math.radians(end_angle)
    draw.ellipse(
        [
            cx + r * math.cos(rad_start) - half_w,
            cy + r * math.sin(rad_start) - half_w,
            cx + r * math.cos(rad_start) + half_w,
            cy + r * math.sin(rad_start) + half_w,
        ],
        fill=track_color,
    )
    draw.ellipse(
        [
            cx + r * math.cos(rad_end) - half_w,
            cy + r * math.sin(rad_end) - half_w,
            cx + r * math.cos(rad_end) + half_w,
            cy + r * math.sin(rad_end) + half_w,
        ],
        fill=track_color,
    )

    # 2. Active progress arc
    if ratio > 0.005:
        active_end = start_angle + ratio * total_span
        draw.arc(bbox, start=start_angle, end=active_end, fill=active_color, width=w)

        # Rounded start cap
        draw.ellipse(
            [
                cx + r * math.cos(rad_start) - half_w,
                cy + r * math.sin(rad_start) - half_w,
                cx + r * math.cos(rad_start) + half_w,
                cy + r * math.sin(rad_start) + half_w,
            ],
            fill=active_color,
        )

        # Illuminated tip knob
        rad_tip = math.radians(active_end)
        kx = cx + r * math.cos(rad_tip)
        ky = cy + r * math.sin(rad_tip)
        knob_r = half_w + 3
        draw.ellipse(
            [kx - knob_r, ky - knob_r, kx + knob_r, ky + knob_r],
            fill=(255, 255, 255),
            outline=active_color,
            width=2,
        )
        draw.ellipse([kx - 2, ky - 2, kx + 2, ky + 2], fill=active_color)


class Home(AbstractLocation):
    """
    Thermostat-Inspired Dual Arc Dashboard.
    Displays real-time ambient temperature and humidity in a dual-arc gauge widget.
    Outer arc: Temperature (gradient from cold blue to hot red).
    Inner arc: Humidity (blue).
    Numbers share identical color coding with their respective gauge bars.
    """

    def __init__(self, db: Optional[Any] = None):
        self.db = db
        self.temperature: Optional[float] = None
        self.humidity: Optional[float] = None

    def handle_knob(self, action: KnobUserAction) -> Optional[str]:
        if action == KnobUserAction.PRESS:
            return "MENU"
        return None

    def render(self, lcd: LCDCore, state: AppState) -> None:
        # Periodic update of current temperature and humidity
        self.temperature = state.temperature
        self.humidity = state.humidity

        bg_color = (11, 15, 25)  # Deep obsidian blue
        img = Image.new("RGB", (lcd.width, lcd.height), bg_color)
        draw = ImageDraw.Draw(img)

        font_header = lcd._get_font(size=14, bold=True)
        font_pill = lcd._get_font(size=10, bold=True)
        font_large_temp = lcd._get_font(size=32, bold=True)
        font_humi = lcd._get_font(size=20, bold=True)
        font_hint = lcd._get_font(size=10, italic=True)

        # ==========================================
        # 1. Header Bar
        # ==========================================
        draw.rectangle((0, 0, lcd.width, 36), fill=(17, 24, 39))
        draw.line([(0, 36), (lcd.width, 36)], fill=(31, 41, 55), width=1)

        draw.text((14, 10), "REMOTE MONITOR", font=font_header, fill=(241, 245, 249))

        # Status Badge (Top-Right)
        badge_text = "LIVE"
        badge_w = 44
        badge_x = lcd.width - badge_w - 10
        draw.rounded_rectangle((badge_x, 8, badge_x + badge_w, 24), radius=4, fill=(19, 78, 74))
        draw.ellipse((badge_x + 6, 14, badge_x + 10, 18), fill=(52, 211, 153))
        draw.text((badge_x + 14, 10), badge_text, font=font_pill, fill=(167, 243, 208))

        # ==========================================
        # 2. Main Thermostat Card Container
        # ==========================================
        card_x0, card_y0 = 10, 42
        card_x1, card_y1 = lcd.width - 10, 276
        draw.rounded_rectangle(
            (card_x0, card_y0, card_x1, card_y1),
            radius=16,
            fill=(19, 23, 34),
            outline=(34, 42, 59),
            width=1,
        )

        cx = lcd.width // 2
        cy = 152

        start_angle = 135
        end_angle = 405

        # Outer arc: Temperature (0°C to 40°C)
        r_temp = 82
        w_temp = 9

        # Inner arc: Humidity (0% to 100%)
        r_humi = 64
        w_humi = 8

        track_color = (29, 36, 51)

        temp_val = self.temperature
        humi_val = self.humidity

        temp_color = get_temp_color(temp_val)
        humi_color = (59, 130, 246)  # Blue

        # Calculate ratios (safely clamped)
        if temp_val is not None and temp_val > 0:
            temp_ratio = max(0.0, min(1.0, (temp_val - 0.0) / 40.0))
        else:
            temp_ratio = 0.0

        if humi_val is not None and humi_val > 0:
            humi_ratio = max(0.0, min(1.0, (humi_val - 0.0) / 100.0))
        else:
            humi_ratio = 0.0

        # Draw outer (Temperature) and inner (Humidity) arcs
        draw_gauge_arc(
            draw, cx, cy, r_temp, w_temp, start_angle, end_angle, temp_ratio, track_color, temp_color
        )
        draw_gauge_arc(
            draw, cx, cy, r_humi, w_humi, start_angle, end_angle, humi_ratio, track_color, humi_color
        )

        # ==========================================
        # 3. Center Metrics Readout
        # ==========================================
        # Temperature number (large, matching temp bar color)
        temp_str = f"{temp_val:.1f}°" if (temp_val is not None and temp_val > 0) else "--.-°"
        bbox_temp = draw.textbbox((0, 0), temp_str, font=font_large_temp)
        tw = bbox_temp[2] - bbox_temp[0]
        draw.text((cx - tw // 2, cy - 26), temp_str, font=font_large_temp, fill=temp_color)

        # Humidity number (sub, matching humi bar color)
        humi_str = f"{humi_val:.0f}%" if (humi_val is not None and humi_val > 0) else "--%"
        bbox_humi = draw.textbbox((0, 0), humi_str, font=font_humi)
        hw = bbox_humi[2] - bbox_humi[0]
        draw.text((cx - hw // 2, cy + 12), humi_str, font=font_humi, fill=humi_color)

        # ==========================================
        # 4. Bottom Navigation Hint (Pill Button)
        # ==========================================
        hint_y = 282
        hint_h = 32
        draw.rounded_rectangle(
            (12, hint_y, lcd.width - 12, hint_y + hint_h),
            radius=8,
            fill=(23, 37, 84),  # Soft navy
            outline=(30, 58, 138),
            width=1,
        )
        draw.text((22, hint_y + 9), "Press knob for Menu", font=font_hint, fill=(191, 219, 254))
        draw_chevron(draw, lcd.width - 26, hint_y + 11, size=5, direction="right", color=(147, 197, 253))

        lcd.render_image(img)