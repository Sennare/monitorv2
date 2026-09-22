import math
from typing import List
from PIL import Image
from soul.moods.robot_eyes import (
    new_frame,
    draw_squircle_eye,
    draw_eyebrow,
    offset_box,
    scale_box,
    DEFAULT_LEFT_BOX,
    DEFAULT_RIGHT_BOX,
)


def get_frames() -> List[Image.Image]:
    """Generate sad robot eyes with sorrowful eyebrows and a smooth running teardrop at 20 FPS (40 frames / 2.0s loop)."""
    frames = []
    total_frames = 40

    for i in range(total_frames):
        img, draw = new_frame()

        # Subtle sorrowful droop oscillation (1px to 2px)
        dy = int(round(1.5 + 0.8 * math.sin(i / total_frames * 2 * math.pi)))

        left_b = offset_box(scale_box(DEFAULT_LEFT_BOX, dh=-2), dy=dy)
        right_b = offset_box(scale_box(DEFAULT_RIGHT_BOX, dh=-2), dy=dy)

        draw_squircle_eye(draw, left_b)
        draw_squircle_eye(draw, right_b)

        # Sad eyebrows slanting up towards the center (\ /)
        brow_y = 11 + dy
        # Subtle eyebrow quiver
        quiver = 1 if (i % 6 in (1, 2)) else 0
        draw_eyebrow(draw, 25, brow_y + 4 + quiver, 53, brow_y + quiver, width=3)
        draw_eyebrow(draw, 75, brow_y + quiver, 103, brow_y + 4 + quiver, width=3)

        # Smooth sliding teardrop under the left eye between frames 10 and 34
        if 10 <= i <= 34:
            t = (i - 10) / 24.0
            tear_start_y = left_b[3] + 2
            tear_y = int(round(tear_start_y + t * 10))
            if tear_y < 62:
                # 2x3 pixel crisp teardrop
                draw.rectangle((36, tear_y, 38, tear_y + 2), fill="white")

        frames.append(img)

    return frames
