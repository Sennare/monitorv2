import math
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
    """Generate aggressive robot eyes with sharp angry eyebrows and tension jitter at 20 FPS (20 frames / 1.0s loop)."""
    frames = []
    total_frames = 20

    # Tension jitter pattern: micro-tremors simulating robotic rage
    jitter_pattern = [
        (0, 0), (1, 0), (0, 0), (-1, 0),
        (0, 0), (0, 1), (0, 0), (1, -1),
        (0, 0), (-1, 0), (0, 0), (0, 0),
        (1, 0), (0, 0), (-1, 1), (0, 0),
        (0, -1), (0, 0), (1, 0), (0, 0),
    ]

    for i in range(total_frames):
        img, draw = new_frame()

        jx, jy = jitter_pattern[i % len(jitter_pattern)]

        # Pulsing eye narrowing from anger tension
        pulse = int(round(math.sin(i / total_frames * 2 * math.pi) * 2.0))
        dh = -4 + pulse

        left_b = offset_box(scale_box(DEFAULT_LEFT_BOX, dh=dh), dx=jx, dy=jy)
        right_b = offset_box(scale_box(DEFAULT_RIGHT_BOX, dh=dh), dx=jx, dy=jy)

        draw_squircle_eye(draw, left_b)
        draw_squircle_eye(draw, right_b)

        # Angry eyebrows slanting down towards center (/ \)
        brow_y = 10 + jy
        # Subtle eyebrow slant fluctuation
        brow_slant = 7 + (1 if i % 4 == 0 else 0)
        draw_eyebrow(draw, 24 + jx, brow_y, 53 + jx, brow_y + brow_slant, width=3)
        draw_eyebrow(draw, 104 + jx, brow_y, 75 + jx, brow_y + brow_slant, width=3)

        frames.append(img)

    return frames
