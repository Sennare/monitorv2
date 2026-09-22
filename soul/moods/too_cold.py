from typing import List
from PIL import Image
from soul.moods.robot_eyes import (
    new_frame,
    draw_chevron_eye,
    LEFT_EYE_CENTER,
    RIGHT_EYE_CENTER,
)


def get_frames() -> List[Image.Image]:
    """Generate shivering freezing robot eyes with > < chevrons and rapid vibration matching Face (4,1)."""
    frames = []
    # Rapid shivering vibration offsets
    shivers = [(-2, 0), (2, -1), (-1, 1), (1, 0)]

    for jx, jy in shivers:
        img, draw = new_frame()

        lx, ly = LEFT_EYE_CENTER[0] + jx, LEFT_EYE_CENTER[1] + jy
        rx, ry = RIGHT_EYE_CENTER[0] + jx, RIGHT_EYE_CENTER[1] + jy

        # Face (4,1): Left eye is '>', Right eye is '<'
        draw_chevron_eye(draw, lx, ly, direction="right", span=20, width=4)
        draw_chevron_eye(draw, rx, ry, direction="left", span=20, width=4)

        frames.append(img)

    return frames
