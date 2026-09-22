from typing import List
from PIL import Image
from soul.moods.robot_eyes import (
    new_frame,
    draw_squircle_eye,
    draw_eyebrow,
    offset_box,
    DEFAULT_LEFT_BOX,
    DEFAULT_RIGHT_BOX,
)


def get_frames() -> List[Image.Image]:
    """Generate sad robot eyes with upward-slanted eyebrows and subtle drooping."""
    frames = []
    # Subtle downward droop on frames
    droop_offsets = [0, 1, 2, 1]

    for i, dy in enumerate(droop_offsets):
        img, draw = new_frame()

        left_b = offset_box(DEFAULT_LEFT_BOX, dy=dy)
        right_b = offset_box(DEFAULT_RIGHT_BOX, dy=dy)

        # Draw sorrowful robot squircle eyes
        draw_squircle_eye(draw, left_b)
        draw_squircle_eye(draw, right_b)

        # Sad eyebrows slanting up towards the center (\ /)
        brow_y = 11 + (dy // 2)
        draw_eyebrow(draw, 25, brow_y + 4, 53, brow_y, width=3)
        draw_eyebrow(draw, 75, brow_y, 103, brow_y + 4, width=3)

        # Subtle teardrop pixel on frame 2
        if i == 2:
            draw.rectangle((38, left_b[3] + 3, 40, left_b[3] + 6), fill="white")

        frames.append(img)

    return frames
