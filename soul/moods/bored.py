import math
from typing import List
from PIL import Image
from soul.moods.robot_eyes import (
    new_frame,
    draw_slit_eye,
    offset_box,
    DEFAULT_LEFT_BOX,
    DEFAULT_RIGHT_BOX,
)


def get_frames() -> List[Image.Image]:
    """Generate bored robot eyes with flat sleepy slits lazily drifting at 20 FPS (40 frames / 2.0s loop)."""
    frames = []
    total_frames = 40

    for i in range(total_frames):
        img, draw = new_frame()

        # Smooth lazy sinusoidal horizontal drift (-4px to +4px)
        dx = int(round(4.0 * math.sin(i / total_frames * 2 * math.pi)))

        # Sleepy lid height easing (5px to 7px, drooping heavier on return sweep)
        h_variation = int(round(math.cos(i / total_frames * 2 * math.pi) * 1.0))
        slit_h = 6 + h_variation

        left_b = offset_box(DEFAULT_LEFT_BOX, dx=dx)
        right_b = offset_box(DEFAULT_RIGHT_BOX, dx=dx)

        draw_slit_eye(draw, left_b, height=slit_h)
        draw_slit_eye(draw, right_b, height=slit_h)

        frames.append(img)

    return frames
