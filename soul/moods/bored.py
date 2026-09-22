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
    """Generate bored robot eyes with flat sleepy slits matching Face (3,2)."""
    frames = []

    for i in range(4):
        img, draw = new_frame()

        if i == 0:
            # Frame 0: Heavy sleepy half-closed eyes
            draw_squircle_eye(draw, scale_box(DEFAULT_LEFT_BOX, dh=-16), radius=5)
            draw_squircle_eye(draw, scale_box(DEFAULT_RIGHT_BOX, dh=-16), radius=5)
        elif i == 1:
            # Frame 1: Flat horizontal slits (Face 3,2)
            draw_slit_eye(draw, DEFAULT_LEFT_BOX, height=6)
            draw_slit_eye(draw, DEFAULT_RIGHT_BOX, height=6)
        elif i == 2:
            # Frame 2: Slits lazily drift left
            draw_slit_eye(draw, offset_box(DEFAULT_LEFT_BOX, dx=-3), height=6)
            draw_slit_eye(draw, offset_box(DEFAULT_RIGHT_BOX, dx=-3), height=6)
        else:
            # Frame 3: Slits lazily drift right
            draw_slit_eye(draw, offset_box(DEFAULT_LEFT_BOX, dx=3), height=6)
            draw_slit_eye(draw, offset_box(DEFAULT_RIGHT_BOX, dx=3), height=6)

        frames.append(img)

    return frames
