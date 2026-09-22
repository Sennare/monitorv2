import math
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
    """Generate overheating robot eyes with exhausted half-lids and a smoothly trickling sweat drop at 20 FPS (30 frames / 1.5s loop)."""
    frames = []
    total_frames = 30

    for i in range(total_frames):
        img, draw = new_frame()

        # Heavy panting / exhaustion lid oscillation
        pant = int(round(math.sin(i / total_frames * 2 * math.pi) * 2.0))
        left_b = offset_box(scale_box(DEFAULT_LEFT_BOX, dh=-10 + pant), dy=4)
        right_b = offset_box(scale_box(DEFAULT_RIGHT_BOX, dh=-10 + pant), dy=4)

        draw_squircle_eye(draw, left_b, radius=5)
        draw_squircle_eye(draw, right_b, radius=5)

        # Sweat drop smoothly trickling down the left temple pixel-by-pixel
        s_y = int(round(16.0 + (i / total_frames) * 32.0))
        drop_x = 16
        draw.line([(drop_x, max(12, s_y - 4)), (drop_x, s_y)], fill="white", width=2)
        draw.ellipse((drop_x - 2, s_y, drop_x + 2, s_y + 4), fill="white")

        frames.append(img)

    return frames
