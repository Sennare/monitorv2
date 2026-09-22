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

        # Squeezed smiling squircle eye with bounce squash & stretch
        # Both outer top border and inner lower border maintain rounded-square (squircle) shape
        if dy >= -1:
            # Landing impact: compressed squash
            dh, dw = -18, 2
            top_th, leg_th = 4, 5
        elif dy <= -4:
            # Apex of bounce: buoyant float
            dh, dw = -14, 1
            top_th, leg_th = 6, 5
        else:
            # Airborne rise/fall
            dh, dw = -16, 0
            top_th, leg_th = 5, 5

        left_b = scale_box(offset_box(DEFAULT_LEFT_BOX, dy=dy), dh=dh, dw=dw)
        right_b = scale_box(offset_box(DEFAULT_RIGHT_BOX, dy=dy), dh=dh, dw=dw)

        # Draw squeezed squircle eyes with rounded-square top and inner bottom borders
        draw_squeezed_squircle_eye(
            draw, left_b, radius=5, inner_radius=3, top_thickness=top_th, leg_thickness=leg_th
        )
        draw_squeezed_squircle_eye(
            draw, right_b, radius=5, inner_radius=3, top_thickness=top_th, leg_thickness=leg_th
        )

        frames.append(img)

    return frames
