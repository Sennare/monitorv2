import math
from typing import List
from PIL import Image
from soul.moods.robot_eyes import (
    new_frame,
    draw_chevron_eye,
    LEFT_EYE_CENTER,
    RIGHT_EYE_CENTER,
)


def get_frames() -> List[Image.Image]:
    """Generate shivering freezing robot eyes with > < chevrons and organic vibration at 20 FPS (20 frames / 1.0s loop)."""
    frames = []
    total_frames = 20

    for i in range(total_frames):
        img, draw = new_frame()

        # High-frequency shivering vibration envelope
        intensity = 1.0 if i < 14 else 0.4
        jx = int(round(intensity * 2.2 * math.sin(i * 3.7)))
        jy = int(round(intensity * 1.5 * math.cos(i * 2.9)))

        # Squeezing shudder span
        span = int(round(20 - 2.0 * abs(math.sin(i / total_frames * math.pi))))

        lx, ly = LEFT_EYE_CENTER[0] + jx, LEFT_EYE_CENTER[1] + jy
        rx, ry = RIGHT_EYE_CENTER[0] + jx, RIGHT_EYE_CENTER[1] + jy

        # Face (4,1): Left eye is '>', Right eye is '<'
        draw_chevron_eye(draw, lx, ly, direction="right", span=span, width=4)
        draw_chevron_eye(draw, rx, ry, direction="left", span=span, width=4)

        frames.append(img)

    return frames
