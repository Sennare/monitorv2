import math
from typing import List
from PIL import Image
from soul.moods.robot_eyes import (
    new_frame,
    draw_squeezed_squircle_eye,
    offset_box,
    scale_box,
    DEFAULT_LEFT_BOX,
    DEFAULT_RIGHT_BOX,
)


def get_frames() -> List[Image.Image]:
    """Generate joyful bouncing robot eyes with happy squeezed squircle eyes at 20 FPS (24 frames / 1.2s loop)."""
    frames = []
    total_frames = 24

    for i in range(total_frames):
        img, draw = new_frame()

        t = i / total_frames
        # Smooth vertical bounce arc peaking at -6 pixels
        dy = -int(round(6.0 * math.sin(t * math.pi)))

        # Squeezed smiling squircle eye base height with bounce squash & stretch
        if dy >= -1:
            # Landing impact: deeper cheek squeeze
            dh = -16
            dw = 2
            squeeze = 0.68
        elif dy <= -4:
            # Apex of bounce: buoyant float squeeze
            dh = -12
            dw = 1
            squeeze = 0.55
        else:
            # Airborne rise/fall
            dh = -14
            dw = 0
            squeeze = 0.60

        left_b = scale_box(offset_box(DEFAULT_LEFT_BOX, dy=dy), dh=dh, dw=dw)
        right_b = scale_box(offset_box(DEFAULT_RIGHT_BOX, dy=dy), dh=dh, dw=dw)

        # Draw squeezed squircle eyes
        draw_squeezed_squircle_eye(draw, left_b, radius=5, squeeze_amount=squeeze)
        draw_squeezed_squircle_eye(draw, right_b, radius=5, squeeze_amount=squeeze)

        frames.append(img)

    return frames
