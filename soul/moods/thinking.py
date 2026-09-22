import math
from typing import List
from PIL import Image
from soul.moods.robot_eyes import (
    new_frame,
    draw_squircle_eye,
    offset_box,
    scale_box,
    DEFAULT_LEFT_BOX,
    DEFAULT_RIGHT_BOX,
)


def get_frames() -> List[Image.Image]:
    """Generate thinking robot eyes looking up-right with cycling digital indicators at 20 FPS (30 frames / 1.5s loop)."""
    frames = []
    total_frames = 30

    dot_xs = [102, 110, 118]
    dot_y = 10

    for i in range(total_frames):
        img, draw = new_frame()

        # Gentle contemplative thinking sway
        sway_x = int(round(5.0 + 0.8 * math.sin(i / total_frames * 2 * math.pi)))
        sway_y = int(round(-5.0 + 0.5 * math.cos(i / total_frames * 2 * math.pi)))

        left_b = offset_box(scale_box(DEFAULT_LEFT_BOX, dh=-2), dx=sway_x, dy=sway_y)
        right_b = offset_box(scale_box(DEFAULT_RIGHT_BOX, dh=-2), dx=sway_x, dy=sway_y)

        draw_squircle_eye(draw, left_b)
        draw_squircle_eye(draw, right_b)

        # Digital loading/processing indicator blocks in top-right
        active_step = (i * 4) // total_frames  # 0, 1, 2, or 3
        for d_idx, x in enumerate(dot_xs):
            is_filled = (d_idx == active_step) or (active_step == 3)
            if is_filled:
                draw.rectangle((x, dot_y, x + 5, dot_y + 5), fill="white")
            else:
                draw.rectangle((x, dot_y, x + 5, dot_y + 5), outline="white", width=1)

        frames.append(img)

    return frames
