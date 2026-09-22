import math
from typing import List
from PIL import Image
from soul.moods.robot_eyes import (
    new_frame,
    draw_squircle_eye,
    draw_slit_eye,
    offset_box,
    scale_box,
    ease_in_out,
    lerp,
    DEFAULT_LEFT_BOX,
    DEFAULT_RIGHT_BOX,
)


def get_frames() -> List[Image.Image]:
    """Generate curious robot eyes with smooth asymmetrical cocked wink and head tilt at 20 FPS (40 frames / 2.0s loop)."""
    frames = []
    total_frames = 40

    for i in range(total_frames):
        img, draw = new_frame()

        # Compute curiosity factor (0.0 = resting, 1.0 = full inquisitive cocked expression)
        if i < 10:
            # Transition into curiosity (0.5s)
            c = ease_in_out(i / 10.0)
        elif i < 28:
            # Hold curiosity with subtle micro-inquiry bob (0.9s)
            bob = math.sin((i - 10) / 18.0 * 2 * math.pi) * 0.05
            c = 1.0 + bob
        else:
            # Transition back to resting (0.6s)
            c = ease_in_out((total_frames - i) / 12.0)

        # Right eye raises and expands inquisitively
        r_dy = -int(round(lerp(0, 3, c)))
        r_dh = int(round(lerp(0, 3, c)))
        r_dw = int(round(lerp(0, 2, c)))
        right_b = offset_box(scale_box(DEFAULT_RIGHT_BOX, dh=r_dh, dw=r_dw), dy=r_dy)
        draw_squircle_eye(draw, right_b)

        # Left eye squashes down into sleek cybernetic slit
        if c > 0.75:
            slit_h = int(round(lerp(8, 6, (c - 0.75) / 0.25)))
            draw_slit_eye(draw, DEFAULT_LEFT_BOX, height=slit_h)
        else:
            l_dh = -int(round(lerp(0, 22, c / 0.75)))
            left_b = scale_box(DEFAULT_LEFT_BOX, dh=l_dh)
            draw_squircle_eye(draw, left_b)

        frames.append(img)

    return frames
