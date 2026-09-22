from PIL import ImageDraw
from typing import Tuple

Color = Tuple[int, int, int]


def draw_home_icon(draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 16, color: Color = (56, 189, 248)) -> None:
    """Draws a crisp modern geometric house icon."""
    # Roof (triangle)
    roof_points = [
        (x + size // 2, y),
        (x + size, y + size // 2),
        (x, y + size // 2),
    ]
    draw.polygon(roof_points, fill=color)

    # Body
    b_left = x + size // 4
    b_right = x + size - size // 4
    b_top = y + size // 2
    b_bottom = y + size
    draw.rectangle((b_left, b_top, b_right, b_bottom), fill=color)

    # Door cutout (empty space in dark background)
    door_w = max(2, size // 4)
    door_h = max(3, size // 3)
    d_left = x + size // 2 - door_w // 2
    d_top = b_bottom - door_h
    draw.rectangle((d_left, d_top, d_left + door_w, b_bottom), fill=(11, 15, 25))


def draw_chart_icon(draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 16, color: Color = (56, 189, 248)) -> None:
    """Draws a modern 3-bar telemetry histogram."""
    bar_w = max(2, size // 5)
    gap = max(1, size // 6)

    # Bar 1 (short)
    h1 = int(size * 0.45)
    draw.rectangle((x, y + size - h1, x + bar_w, y + size), fill=color)

    # Bar 2 (medium)
    h2 = int(size * 0.75)
    x2 = x + bar_w + gap
    draw.rectangle((x2, y + size - h2, x2 + bar_w, y + size), fill=color)

    # Bar 3 (tall)
    h3 = size
    x3 = x2 + bar_w + gap
    draw.rectangle((x3, y + size - h3, x3 + bar_w, y + size), fill=color)


def draw_settings_icon(draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 16, color: Color = (56, 189, 248)) -> None:
    """Draws sleek modern tech sliders/faders."""
    h = size
    # Top slider track
    y1 = y + int(h * 0.3)
    draw.line([(x, y1), (x + size, y1)], fill=color, width=1)
    # Top slider knob
    draw.rectangle((x + int(size * 0.3), y1 - 2, x + int(size * 0.45), y1 + 2), fill=color)

    # Bottom slider track
    y2 = y + int(h * 0.7)
    draw.line([(x, y2), (x + size, y2)], fill=color, width=1)
    # Bottom slider knob
    draw.rectangle((x + int(size * 0.65), y2 - 2, x + int(size * 0.8), y2 + 2), fill=color)


def draw_mascot_icon(draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 16, color: Color = (56, 189, 248)) -> None:
    """Draws a cute minimalist cat head with pointed ears."""
    # Left ear
    draw.polygon([(x + 2, y + 6), (x + 5, y), (x + 7, y + 6)], fill=color)
    # Right ear
    draw.polygon([(x + size - 8, y + 6), (x + size - 6, y), (x + size - 3, y + 6)], fill=color)
    # Head (rounded ellipse)
    draw.ellipse((x + 1, y + 4, x + size - 2, y + size), fill=color)


def draw_temp_icon(draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 16, color: Color = (251, 146, 60)) -> None:
    """Draws a sleek thermometer symbol."""
    center_x = x + size // 2
    # Upper tube
    tube_w = max(2, size // 4)
    draw.rectangle((center_x - tube_w // 2, y, center_x + tube_w // 2, y + int(size * 0.65)), fill=color)
    # Bulb
    bulb_r = max(3, int(size * 0.28))
    draw.ellipse((center_x - bulb_r, y + size - bulb_r * 2, center_x + bulb_r, y + size), fill=color)


def draw_humidity_icon(draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 16, color: Color = (56, 189, 248)) -> None:
    """Draws a sleek minimalist teardrop."""
    cx = x + size // 2
    # Upper triangular tip
    draw.polygon([(cx, y + 1), (x + 2, y + int(size * 0.65)), (x + size - 2, y + int(size * 0.65))], fill=color)
    # Bottom rounded curve
    draw.ellipse((x + 2, y + int(size * 0.35), x + size - 2, y + size), fill=color)


def draw_presence_radar(draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 16, active: bool = True) -> None:
    """Draws a sleek radar / proximity sensor badge."""
    cx = x + size // 2
    cy = y + size // 2
    center_color = (74, 222, 128) if active else (100, 116, 139)
    ring_color = (22, 101, 52) if active else (51, 65, 85)

    # Outer soft glow ring
    draw.ellipse((x, y, x + size, y + size), outline=ring_color, width=1)
    # Middle ring
    r_mid = int(size * 0.25)
    draw.ellipse((cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid), outline=center_color, width=1)
    # Center dot
    r_core = max(1, size // 8)
    draw.ellipse((cx - r_core, cy - r_core, cx + r_core, cy + r_core), fill=center_color)


def draw_heart_icon(draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 16, color: Color = (244, 114, 182)) -> None:
    """Draws a clean geometric heart."""
    # Left lobe
    r = size // 4
    draw.ellipse((x + 1, y, x + 1 + r * 2, y + r * 2), fill=color)
    # Right lobe
    draw.ellipse((x + size - 1 - r * 2, y, x + size - 1, y + r * 2), fill=color)
    # Bottom triangle
    draw.polygon([(x + 2, y + r), (x + size - 2, y + r), (x + size // 2, y + size)], fill=color)


def draw_warning_icon(draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 16, color: Color = (239, 68, 68)) -> None:
    """Draws a sharp alert triangle with inner exclamation point."""
    # Outer Triangle
    tri_points = [
        (x + size // 2, y),
        (x + size, y + size),
        (x, y + size),
    ]
    draw.polygon(tri_points, fill=color)

    # Inner exclamation mark
    cx = x + size // 2
    draw.line([(cx, y + int(size * 0.35)), (cx, y + int(size * 0.68))], fill=(24, 12, 16), width=2)
    draw.point((cx, y + int(size * 0.82)), fill=(24, 12, 16))


def draw_chevron(draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 8, direction: str = "right", color: Color = (148, 163, 184), width: int = 2) -> None:
    """Draws a minimal clean arrow chevron: right '>' or left '<'."""
    if direction == "right":
        points = [(x, y), (x + size, y + size), (x, y + size * 2)]
    else:
        points = [(x + size, y), (x, y + size), (x + size, y + size * 2)]
    draw.line(points, fill=color, width=width)
