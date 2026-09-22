import time
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw

from ..abstract_location import AbstractLocation
from display.lcd_core import LCDCore
from display.ui_icons import (
    draw_temp_icon,
    draw_humidity_icon,
    draw_chevron,
)
from state import AppState, KnobUserAction
from database.database import Database


def bin_and_average_slots(
    raw_data: List[Tuple[datetime, Optional[float], Optional[float]]],
    start_time: datetime,
    end_time: datetime,
    width_px: int,
) -> Tuple[List[Optional[float]], List[Optional[float]]]:
    """
    Splits the time interval [start_time, end_time] into `width_px` discrete time slots,
    groups measurement rows into their respective slots, calculates the average
    temperature and humidity for each slot, and linearly interpolates missing interior points.
    """
    if width_px <= 0:
        return [], []

    total_seconds = (end_time - start_time).total_seconds()
    if total_seconds <= 0:
        return [None] * width_px, [None] * width_px

    seconds_per_slot = total_seconds / float(width_px)

    temp_bins: List[List[float]] = [[] for _ in range(width_px)]
    humi_bins: List[List[float]] = [[] for _ in range(width_px)]

    for row in raw_data:
        if len(row) < 3:
            continue
        db_time, temp, humi = row[0], row[1], row[2]
        if hasattr(db_time, "tzinfo") and db_time.tzinfo is not None:
            db_time = db_time.replace(tzinfo=None)

        diff_sec = (db_time - start_time).total_seconds()
        if 0 <= diff_sec < total_seconds:
            slot_idx = int(diff_sec / seconds_per_slot)
            if 0 <= slot_idx < width_px:
                if temp is not None:
                    try:
                        temp_bins[slot_idx].append(float(temp))
                    except (ValueError, TypeError):
                        pass
                if humi is not None:
                    try:
                        humi_bins[slot_idx].append(float(humi))
                    except (ValueError, TypeError):
                        pass

    # Compute averages per slot
    temp_avg: List[Optional[float]] = [
        sum(temp_bins[i]) / len(temp_bins[i]) if temp_bins[i] else None
        for i in range(width_px)
    ]
    humi_avg: List[Optional[float]] = [
        sum(humi_bins[i]) / len(humi_bins[i]) if humi_bins[i] else None
        for i in range(width_px)
    ]

    # Linearly interpolate gaps between valid slots
    def _interpolate(series: List[Optional[float]]) -> List[Optional[float]]:
        result = list(series)
        valid_indices = [i for i, val in enumerate(result) if val is not None]
        if len(valid_indices) < 2:
            return result

        for k in range(len(valid_indices) - 1):
            i0 = valid_indices[k]
            i1 = valid_indices[k + 1]
            if i1 - i0 > 1:
                v0 = result[i0]
                v1 = result[i1]
                step = (v1 - v0) / float(i1 - i0)
                for step_idx, slot in enumerate(range(i0 + 1, i1), start=1):
                    result[slot] = v0 + step * step_idx

        return result

    return _interpolate(temp_avg), _interpolate(humi_avg)


class Home(AbstractLocation):
    """
    Modern Minimalist Status Dashboard with 24-Hour Telemetry Graph.
    Displays live ambient metrics and a continuous dual-line graph (Temp & Humidity)
    binned per screen pixel width. Rotating the knob navigates through historical time,
    and pressing the knob opens the Menu.
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db if db is not None else Database()
        self.hours_offset: int = 0
        self._cache: dict = {}

    def on_enter(self) -> None:
        """Reset time travel to 'now' whenever entering Home."""
        self.hours_offset = 0

    def reset_time_travel(self) -> None:
        """Reset time travel back to 'now'."""
        self.hours_offset = 0

    def handle_knob(self, action: KnobUserAction) -> Optional[str]:
        if action == KnobUserAction.TURN_LEFT:
            # Scroll back in time
            self.hours_offset += 1
            return None
        elif action == KnobUserAction.TURN_RIGHT:
            # Scroll forward in time, hard-capped at 0 ("now")
            self.hours_offset = max(0, self.hours_offset - 1)
            return None
        elif action == KnobUserAction.PRESS:
            return "MENU"
        return None

    def render(self, lcd: LCDCore, state: AppState) -> None:
        bg_color = (11, 15, 25)  # Deep obsidian blue
        img = Image.new("RGB", (lcd.width, lcd.height), bg_color)
        draw = ImageDraw.Draw(img)

        font_header = lcd._get_font(size=14, bold=True)
        font_pill = lcd._get_font(size=10, bold=True)
        font_large = lcd._get_font(size=20, bold=True)
        font_card_title = lcd._get_font(size=10, bold=True)
        font_subtext = lcd._get_font(size=9, bold=False)
        font_tiny = lcd._get_font(size=8, bold=False)
        font_hint = lcd._get_font(size=10, italic=True)

        now = datetime.now()
        end_time = now - timedelta(hours=self.hours_offset)
        start_time = end_time - timedelta(hours=24)

        # ==========================================
        # 1. Header Bar
        # ==========================================
        draw.rectangle((0, 0, lcd.width, 36), fill=(17, 24, 39))
        draw.line([(0, 36), (lcd.width, 36)], fill=(31, 41, 55), width=1)

        draw.text((14, 10), "REMOTE MONITOR", font=font_header, fill=(241, 245, 249))

        # Status Badge (Top-Right)
        if self.hours_offset == 0:
            badge_text = "LIVE"
            badge_w = 44
            badge_x = lcd.width - badge_w - 10
            draw.rounded_rectangle((badge_x, 8, badge_x + badge_w, 24), radius=4, fill=(19, 78, 74))
            draw.ellipse((badge_x + 6, 14, badge_x + 10, 18), fill=(52, 211, 153))
            draw.text((badge_x + 14, 10), badge_text, font=font_pill, fill=(167, 243, 208))
        else:
            badge_text = f"-{self.hours_offset}h"
            badge_w = 48
            badge_x = lcd.width - badge_w - 10
            draw.rounded_rectangle((badge_x, 8, badge_x + badge_w, 24), radius=4, fill=(69, 26, 3))
            draw.ellipse((badge_x + 6, 14, badge_x + 10, 18), fill=(251, 146, 60))
            draw.text((badge_x + 14, 10), badge_text, font=font_pill, fill=(254, 215, 170))

        # ==========================================
        # 2. Environmental Metrics Cards (Current Readings)
        # ==========================================
        card_w = (lcd.width - 32) // 2
        card_y = 42
        card_h = 66

        # --- Temperature Card (Left) ---
        x_temp = 12
        draw.rounded_rectangle(
            (x_temp, card_y, x_temp + card_w, card_y + card_h),
            radius=8,
            fill=(17, 24, 39),
            outline=(31, 41, 55),
            width=1,
        )
        draw_temp_icon(draw, x_temp + 10, card_y + 8, size=13, color=(251, 146, 60))
        draw.text((x_temp + 28, card_y + 8), "TEMP", font=font_card_title, fill=(156, 163, 175))

        temp_str = f"{state.temperature:.1f}°" if state.temperature else "--.-°"
        draw.text((x_temp + 10, card_y + 26), temp_str, font=font_large, fill=(251, 191, 36))
        draw.text((x_temp + 10, card_y + 50), "CELSIUS", font=font_subtext, fill=(107, 114, 128))

        # --- Humidity Card (Right) ---
        x_humi = x_temp + card_w + 8
        draw.rounded_rectangle(
            (x_humi, card_y, x_humi + card_w, card_y + card_h),
            radius=8,
            fill=(17, 24, 39),
            outline=(31, 41, 55),
            width=1,
        )
        draw_humidity_icon(draw, x_humi + 10, card_y + 8, size=13, color=(56, 189, 248))
        draw.text((x_humi + 28, card_y + 8), "HUMIDITY", font=font_card_title, fill=(156, 163, 175))

        humi_str = f"{state.humidity:.0f}%" if state.humidity else "--%"
        draw.text((x_humi + 10, card_y + 26), humi_str, font=font_large, fill=(56, 189, 248))
        draw.text((x_humi + 10, card_y + 50), "RELATIVE", font=font_subtext, fill=(107, 114, 128))

        # ==========================================
        # 3. 24-Hour Dual-Line Graph
        # ==========================================
        graph_card_x = 12
        graph_card_y = 114
        graph_card_w = lcd.width - 24
        graph_card_h = 162

        draw.rounded_rectangle(
            (graph_card_x, graph_card_y, graph_card_x + graph_card_w, graph_card_y + graph_card_h),
            radius=8,
            fill=(17, 24, 39),
            outline=(31, 41, 55),
            width=1,
        )

        # Graph Header inside Card
        draw.text((graph_card_x + 10, graph_card_y + 8), "24H TREND", font=font_card_title, fill=(156, 163, 175))

        # Legend: Amber Temp & Cyan Humidity
        leg_temp_x = graph_card_x + 92
        draw.ellipse((leg_temp_x, graph_card_y + 11, leg_temp_x + 6, graph_card_y + 17), fill=(251, 191, 36))
        draw.text((leg_temp_x + 9, graph_card_y + 8), "Temp (°C)", font=font_subtext, fill=(209, 213, 219))

        leg_humi_x = leg_temp_x + 58
        draw.ellipse((leg_humi_x, graph_card_y + 11, leg_humi_x + 6, graph_card_y + 17), fill=(56, 189, 248))
        draw.text((leg_humi_x + 9, graph_card_y + 8), "Humi (%)", font=font_subtext, fill=(209, 213, 219))

        # Plot bounding box
        plot_x0 = graph_card_x + 30
        plot_x1 = graph_card_x + graph_card_w - 12
        plot_w = plot_x1 - plot_x0
        plot_y0 = graph_card_y + 26
        plot_y1 = graph_card_y + graph_card_h - 22
        plot_h = plot_y1 - plot_y0

        # Background gridlines (4 horizontal lines: 0%, 33%, 66%, 100%)
        for pct in [0.0, 0.33, 0.66, 1.0]:
            gy = int(plot_y1 - pct * plot_h)
            draw.line([(plot_x0, gy), (plot_x1, gy)], fill=(31, 41, 55), width=1)

        # Y-Axis Scale Labels (Left)
        draw.text((graph_card_x + 6, plot_y0 - 4), "50°", font=font_tiny, fill=(107, 114, 128))
        draw.text((graph_card_x + 6, plot_y0 + int(plot_h * 0.5) - 4), "25°", font=font_tiny, fill=(107, 114, 128))
        draw.text((graph_card_x + 6, plot_y1 - 4), "0°", font=font_tiny, fill=(107, 114, 128))

        # Time Scale Labels (Bottom)
        t_start_label = start_time.strftime("%H:%M")
        t_end_label = "NOW" if self.hours_offset == 0 else end_time.strftime("%H:%M")
        draw.text((plot_x0, plot_y1 + 4), t_start_label, font=font_tiny, fill=(107, 114, 128))
        draw.text((plot_x0 + (plot_w // 2) - 10, plot_y1 + 4), "-12h", font=font_tiny, fill=(107, 114, 128))
        draw.text((plot_x1 - 24, plot_y1 + 4), t_end_label, font=font_tiny, fill=(107, 114, 128))

        # Retrieve Telemetry & Bin into Pixel Slots
        cache_key = (self.hours_offset, int(time.time() // 30))
        if cache_key in self._cache:
            temp_line, humi_line = self._cache[cache_key]
        else:
            try:
                raw_data = self.db.fetch_time_range(start_time, end_time)
            except Exception:
                raw_data = []
            temp_line, humi_line = bin_and_average_slots(raw_data, start_time, end_time, plot_w)
            # Prune old cache entries
            if len(self._cache) > 20:
                self._cache.clear()
            self._cache[cache_key] = (temp_line, humi_line)

        has_temp_data = any(v is not None for v in temp_line)
        has_humi_data = any(v is not None for v in humi_line)

        if not has_temp_data and not has_humi_data:
            msg = "No telemetry for this period"
            draw.text((plot_x0 + 16, plot_y0 + (plot_h // 2) - 6), msg, font=font_subtext, fill=(107, 114, 128))
        else:
            # Temperature scale: 0°C to 50°C
            def temp_to_y(temp_val: float) -> int:
                clamped = max(0.0, min(50.0, temp_val))
                return int(plot_y1 - (clamped / 50.0) * plot_h)

            # Humidity scale: 0% to 100%
            def humi_to_y(humi_val: float) -> int:
                clamped = max(0.0, min(100.0, humi_val))
                return int(plot_y1 - (clamped / 100.0) * plot_h)

            # Draw Humidity Line (Cyan)
            humi_color = (56, 189, 248)
            for x in range(plot_w - 1):
                y0 = humi_line[x]
                y1 = humi_line[x + 1]
                if y0 is not None and y1 is not None:
                    px0 = plot_x0 + x
                    px1 = plot_x0 + x + 1
                    py0 = humi_to_y(y0)
                    py1 = humi_to_y(y1)
                    draw.line([(px0, py0), (px1, py1)], fill=humi_color, width=2)

            # Draw Temperature Line (Amber)
            temp_color = (251, 191, 36)
            for x in range(plot_w - 1):
                y0 = temp_line[x]
                y1 = temp_line[x + 1]
                if y0 is not None and y1 is not None:
                    px0 = plot_x0 + x
                    px1 = plot_x0 + x + 1
                    py0 = temp_to_y(y0)
                    py1 = temp_to_y(y1)
                    draw.line([(px0, py0), (px1, py1)], fill=temp_color, width=2)

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
        draw.text((22, hint_y + 9), "Knob: ◄► History  •  Press: Menu", font=font_hint, fill=(191, 219, 254))
        draw_chevron(draw, lcd.width - 26, hint_y + 11, size=5, direction="right", color=(147, 197, 253))

        lcd.render_image(img)