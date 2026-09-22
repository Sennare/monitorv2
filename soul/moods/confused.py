from typing import List
from PIL import Image
from soul.moods.robot_eyes import (
    new_frame,
    draw_spiral_eye,
    LEFT_EYE_CENTER,
    RIGHT_EYE_CENTER,
)


def get_frames() -> List[Image.Image]:
    """Generate confused/dizzy robot eyes with spinning concentric rings matching Face (4,3)."""
    frames = []

    for phase in range(4):
        img, draw = new_frame()

        draw_spiral_eye(draw, LEFT_EYE_CENTER[0], LEFT_EYE_CENTER[1], phase=phase)
        draw_spiral_eye(draw, RIGHT_EYE_CENTER[0], RIGHT_EYE_CENTER[1], phase=phase)

        frames.append(img)

    return frames
