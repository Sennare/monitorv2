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
    """Generate overheating robot eyes with exhausted half-lids and dripping sweat drop."""
    frames = []
    sweat_drop_ys = [18, 24, 30, 36]

    for i, s_y in enumerate(sweat_drop_ys):
        img, draw = new_frame()

        # Drooping exhausted half-lidded eyes
        left_b = offset_box(scale_box(DEFAULT_LEFT_BOX, dh=-10), dy=4)
        right_b = offset_box(scale_box(DEFAULT_RIGHT_BOX, dh=-10), dy=4)

        draw_squircle_eye(draw, left_b, radius=5)
        draw_squircle_eye(draw, right_b, radius=5)

        # Digital sweat drop running down the left temple/screen edge
        drop_x = 16
        draw.line([(drop_x, s_y - 4), (drop_x, s_y)], fill="white", width=2)
        draw.ellipse((drop_x - 2, s_y, drop_x + 2, s_y + 4), fill="white")

        frames.append(img)

    return frames
