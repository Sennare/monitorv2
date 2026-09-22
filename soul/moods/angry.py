from typing import List
from PIL import Image
from soul.moods.robot_eyes import (
    new_frame,
    draw_squircle_eye,
    draw_eyebrow,
    offset_box,
    scale_box,
    DEFAULT_LEFT_BOX,
    DEFAULT_RIGHT_BOX,
)


def get_frames() -> List[Image.Image]:
    """Generate aggressive robot eyes with sharp angry eyebrows and tension jitter."""
    frames = []
    # Micro jitter representing robotic rage
    jitters = [(0, 0), (1, 0), (-1, 0), (0, 1)]

    for i, (jx, jy) in enumerate(jitters):
        img, draw = new_frame()

        # Eyes slightly tense and narrow on middle frames
        dh = -4 if i in (1, 2) else -2
        left_b = offset_box(scale_box(DEFAULT_LEFT_BOX, dh=dh), dx=jx, dy=jy)
        right_b = offset_box(scale_box(DEFAULT_RIGHT_BOX, dh=dh), dx=jx, dy=jy)

        draw_squircle_eye(draw, left_b)
        draw_squircle_eye(draw, right_b)

        # Angry eyebrows slanting down towards center (/ \)
        brow_y = 10 + jy
        draw_eyebrow(draw, 24 + jx, brow_y, 53 + jx, brow_y + 7, width=3)
        draw_eyebrow(draw, 104 + jx, brow_y, 75 + jx, brow_y + 7, width=3)

        frames.append(img)

    return frames
