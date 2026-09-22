from typing import List
from PIL import Image
from soul.moods.robot_eyes import (
    new_frame,
    draw_squircle_eye,
    draw_slit_eye,
    offset_box,
    scale_box,
    DEFAULT_LEFT_BOX,
    DEFAULT_RIGHT_BOX,
)


def get_frames() -> List[Image.Image]:
    """Generate curious robot eyes with asymmetrical cocked wink and head tilt."""
    frames = []

    for i in range(4):
        img, draw = new_frame()

        if i == 0:
            # Frame 0: Resting eyes with slight curiosity height difference
            draw_squircle_eye(draw, scale_box(DEFAULT_LEFT_BOX, dh=-4))
            draw_squircle_eye(draw, DEFAULT_RIGHT_BOX)
        elif i == 1:
            # Frame 1: Left eye narrows halfway, right eye widens
            draw_squircle_eye(draw, scale_box(DEFAULT_LEFT_BOX, dh=-14))
            draw_squircle_eye(draw, offset_box(DEFAULT_RIGHT_BOX, dy=-2))
        elif i == 2:
            # Frame 2: Full cocked expression (Left eye is sleek slit, Right eye is wide squircle)
            draw_slit_eye(draw, DEFAULT_LEFT_BOX, height=6)
            draw_squircle_eye(draw, offset_box(scale_box(DEFAULT_RIGHT_BOX, dh=2), dy=-3))
        else:
            # Frame 3: Left eye reopening
            draw_squircle_eye(draw, scale_box(DEFAULT_LEFT_BOX, dh=-10))
            draw_squircle_eye(draw, DEFAULT_RIGHT_BOX)

        frames.append(img)

    return frames
