import math
from typing import Tuple
from PIL import Image, ImageDraw

OLED_WIDTH = 128
OLED_HEIGHT = 64

# Standard eye centers
LEFT_EYE_CENTER = (40, 32)
RIGHT_EYE_CENTER = (88, 32)

# Default squircle eye bounding boxes (width=28, height=30)
DEFAULT_LEFT_BOX = (26, 17, 54, 47)
DEFAULT_RIGHT_BOX = (74, 17, 102, 47)
DEFAULT_RADIUS = 7


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b for t in [0.0, 1.0]."""
    return a + (b - a) * t


def ease_in_out(t: float) -> float:
    """Smooth S-curve ease-in-out (smoothstep) for t in [0.0, 1.0]."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def interpolate_box(box_a: Tuple[int, int, int, int], box_b: Tuple[int, int, int, int], t: float) -> Tuple[int, int, int, int]:
    """Smoothly interpolate between two bounding boxes with easing."""
    e = ease_in_out(t)
    return (
        int(round(lerp(box_a[0], box_b[0], e))),
        int(round(lerp(box_a[1], box_b[1], e))),
        int(round(lerp(box_a[2], box_b[2], e))),
        int(round(lerp(box_a[3], box_b[3], e))),
    )


def new_frame() -> Tuple[Image.Image, ImageDraw.ImageDraw]:
    """Create a blank monochrome 128x64 OLED frame buffer."""
    img = Image.new("1", (OLED_WIDTH, OLED_HEIGHT), 0)
    draw = ImageDraw.Draw(img)
    return img, draw


def offset_box(box: Tuple[int, int, int, int], dx: int = 0, dy: int = 0) -> Tuple[int, int, int, int]:
    """Translate a bounding box by dx and dy."""
    x0, y0, x1, y1 = box
    return (x0 + dx, y0 + dy, x1 + dx, y1 + dy)


def scale_box(box: Tuple[int, int, int, int], dh: int = 0, dw: int = 0) -> Tuple[int, int, int, int]:
    """Expand or shrink box height/width around its vertical and horizontal center."""
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2
    w = (x1 - x0) + dw
    h = (y1 - y0) + dh
    return (cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2)


def draw_squircle_eye(
    draw: ImageDraw.ImageDraw,
    box: Tuple[int, int, int, int],
    radius: int = DEFAULT_RADIUS,
    fill: str = "white"
) -> None:
    """Draw a solid rounded rectangle (squircle) robot eye."""
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def draw_squeezed_squircle_eye(
    draw: ImageDraw.ImageDraw,
    box: Tuple[int, int, int, int],
    radius: int = 5,
    inner_radius: int = 3,
    top_thickness: int = 5,
    leg_thickness: int = 5,
    fill: str = "white",
) -> None:
    """
    Draw a happy/smiling squeezed squircle eye.
    Both the top outer border and the inner lower cutout border follow a rounded-square
    (squircle) geometry with flat edges and rounded corners.
    """
    x0, y0, x1, y1 = box
    # Outer rounded square (squircle)
    draw.rounded_rectangle(box, radius=radius, fill=fill)

    # Inner rounded square cutout from the bottom
    cut_x0 = x0 + leg_thickness
    cut_x1 = x1 - leg_thickness
    cut_y0 = y0 + top_thickness
    cut_y1 = y1 + 10  # extends below bottom to keep legs open
    draw.rounded_rectangle((cut_x0, cut_y0, cut_x1, cut_y1), radius=inner_radius, fill=0)


def draw_slit_eye(
    draw: ImageDraw.ImageDraw,
    box: Tuple[int, int, int, int],
    height: int = 6,
    radius: int = 3,
    fill: str = "white"
) -> None:
    """Draw a thin horizontal bar/slit eye (sleeping/bored/squint)."""
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    w = box[2] - box[0]
    slit_box = (cx - w // 2, cy - height // 2, cx + w // 2, cy + height // 2)
    draw.rounded_rectangle(slit_box, radius=radius, fill=fill)


def draw_arch_eye(
    draw: ImageDraw.ImageDraw,
    box: Tuple[int, int, int, int],
    width: int = 5,
    fill: str = "white"
) -> None:
    """Draw a curved upward smiling arc eye (⌒ ⌒)."""
    # Pillow draw.arc uses 0 as 3 o'clock, 180 as 9 o'clock, 270 as 12 o'clock
    # start=185, end=355 forms an upward-arching eye
    draw.arc(box, start=185, end=355, fill=fill, width=width)


def draw_dome_eye(
    draw: ImageDraw.ImageDraw,
    box: Tuple[int, int, int, int],
    fill: str = "white"
) -> None:
    """Draw a dome-shaped eye with curved top and flat bottom."""
    draw.chord(box, start=180, end=0, fill=fill)


def draw_chevron_eye(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    direction: str = "right",
    span: int = 18,
    width: int = 4,
    fill: str = "white"
) -> None:
    """Draw a thick chevron eye (> or <) for squinting/shivering cold."""
    hw = span // 2
    hh = span // 2 + 3
    if direction == "right":  # '>'
        pts = [(cx - hw, cy - hh), (cx + hw, cy), (cx - hw, cy + hh)]
    else:  # '<'
        pts = [(cx + hw, cy - hh), (cx - hw, cy), (cx + hw, cy + hh)]
    draw.line(pts, fill=fill, width=width)


def draw_spiral_eye(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    phase: int = 0,
    fill: str = "white",
    r_outer: int = None,
    r_mid: int = None,
    r_inner: int = 3,
    pupil_offset: Tuple[int, int] = (0, 0),
) -> None:
    """Draw concentric spiral/ring eyes for confusion/dizziness."""
    if r_outer is None:
        r_outer = 14 + (phase % 2)
    if r_mid is None:
        r_mid = 8 - (phase % 2)
    draw.ellipse((cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer), outline=fill, width=3)
    draw.ellipse((cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid), outline=fill, width=2)
    px, py = cx + pupil_offset[0], cy + pupil_offset[1]
    draw.ellipse((px - r_inner, py - r_inner, px + r_inner, py + r_inner), fill=fill)


def draw_eyebrow(
    draw: ImageDraw.ImageDraw,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    width: int = 3,
    fill: str = "white"
) -> None:
    """Draw an angled cybernetic eyebrow line."""
    draw.line([(x0, y0), (x1, y1)], fill=fill, width=width)
