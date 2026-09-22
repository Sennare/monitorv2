from typing import List
from PIL import Image
from soul.moods.robot_eyes import (
    new_frame,
    draw_dome_eye,
    draw_arch_eye,
    offset_box,
    DEFAULT_LEFT_BOX,
    DEFAULT_RIGHT_BOX,
)


def get_frames() -> List[Image.Image]:
    """Generate joyful bouncing robot eyes with smiling arcs and happy domes."""
    frames = []
    bounce_offsets = [0, -3, -4, -1]

    for i, dy in enumerate(bounce_offsets):
        img, draw = new_frame()

        left_b = offset_box(DEFAULT_LEFT_BOX, dy=dy)
        right_b = offset_box(DEFAULT_RIGHT_BOX, dy=dy)

        if i % 2 == 0:
            # Filled cheerful dome eyes (curved top, flat bottom)
            draw_dome_eye(draw, left_b)
            draw_dome_eye(draw, right_b)
        else:
            # Upward curving smiling arcs
            draw_arch_eye(draw, left_b, width=5)
            draw_arch_eye(draw, right_b, width=5)

        frames.append(img)

    return frames
