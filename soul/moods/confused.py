import math
from typing import List
from PIL import Image
from soul.moods.robot_eyes import (
    new_frame,
    draw_spiral_eye,
    LEFT_EYE_CENTER,
    RIGHT_EYE_CENTER,
)


def get_frames() -> List[Image.Image]:
    """Generate confused/dizzy robot eyes with hypnotic rotating spiral rings at 20 FPS (24 frames / 1.2s loop)."""
    frames = []
    total_frames = 24

    for i in range(total_frames):
        img, draw = new_frame()

        angle = 2.0 * math.pi * (i / total_frames)

        # Pulsating concentric wave ripples
        r_outer = int(round(14.0 + 2.0 * math.sin(angle)))
        r_mid = int(round(8.0 + 1.5 * math.cos(angle)))

        # Dizzy orbiting pupil center
        p_dx = int(round(1.5 * math.cos(angle)))
        p_dy = int(round(1.5 * math.sin(angle)))

        draw_spiral_eye(
            draw,
            LEFT_EYE_CENTER[0],
            LEFT_EYE_CENTER[1],
            phase=i,
            r_outer=r_outer,
            r_mid=r_mid,
            pupil_offset=(p_dx, p_dy),
        )
        draw_spiral_eye(
            draw,
            RIGHT_EYE_CENTER[0],
            RIGHT_EYE_CENTER[1],
            phase=i,
            r_outer=r_outer,
            r_mid=r_mid,
            pupil_offset=(p_dx, p_dy),
        )

        frames.append(img)

    return frames
