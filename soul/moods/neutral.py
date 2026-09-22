from typing import List
from PIL import Image
from soul.moods.robot_eyes import (
    new_frame,
    draw_squircle_eye,
    draw_slit_eye,
    scale_box,
    DEFAULT_LEFT_BOX,
    DEFAULT_RIGHT_BOX,
)


def get_frames() -> List[Image.Image]:
    """Generate neutral robot eye frames with natural blinking and idle gaze."""
    frames = []

    # 8-frame loop at 0.5s per frame (4 seconds total cycle)
    for i in range(8):
        img, draw = new_frame()

        if i in (0, 1):
            # Frame 0-1: Normal fully open resting squircle eyes
            draw_squircle_eye(draw, DEFAULT_LEFT_BOX)
            draw_squircle_eye(draw, DEFAULT_RIGHT_BOX)
        elif i == 2:
            # Frame 2: Half-blink (closing)
            draw_squircle_eye(draw, scale_box(DEFAULT_LEFT_BOX, dh=-14))
            draw_squircle_eye(draw, scale_box(DEFAULT_RIGHT_BOX, dh=-14))
        elif i == 3:
            # Frame 3: Closed blink (horizontal slit)
            draw_slit_eye(draw, DEFAULT_LEFT_BOX, height=6)
            draw_slit_eye(draw, DEFAULT_RIGHT_BOX, height=6)
        elif i == 4:
            # Frame 4: Half-blink (reopening)
            draw_squircle_eye(draw, scale_box(DEFAULT_LEFT_BOX, dh=-14))
            draw_squircle_eye(draw, scale_box(DEFAULT_RIGHT_BOX, dh=-14))
        else:
            # Frames 5, 6, 7: Fully open resting eyes
            draw_squircle_eye(draw, DEFAULT_LEFT_BOX)
            draw_squircle_eye(draw, DEFAULT_RIGHT_BOX)

        frames.append(img)

    return frames