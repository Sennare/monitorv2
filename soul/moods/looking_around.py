from typing import List
from PIL import Image
from soul.moods.robot_eyes import (
    new_frame,
    draw_squircle_eye,
    draw_slit_eye,
    offset_box,
    DEFAULT_LEFT_BOX,
    DEFAULT_RIGHT_BOX,
)


def get_frames() -> List[Image.Image]:
    """Generate looking around robot eye animation cleanly scanning the environment."""
    frames = []

    # 8-step scan sequence
    steps = [
        ("center", 0, 0),
        ("left", -7, 0),
        ("far_left", -12, 0),
        ("center", 0, 0),
        ("right", 7, 0),
        ("far_right", 12, 0),
        ("up", 0, -5),
        ("blink", 0, 0),
    ]

    for mode, dx, dy in steps:
        img, draw = new_frame()

        if mode == "blink":
            # Quick cybernetic blink during scan
            draw_slit_eye(draw, DEFAULT_LEFT_BOX, height=6)
            draw_slit_eye(draw, DEFAULT_RIGHT_BOX, height=6)
        else:
            left_b = offset_box(DEFAULT_LEFT_BOX, dx=dx, dy=dy)
            right_b = offset_box(DEFAULT_RIGHT_BOX, dx=dx, dy=dy)
            draw_squircle_eye(draw, left_b)
            draw_squircle_eye(draw, right_b)

        frames.append(img)

    return frames