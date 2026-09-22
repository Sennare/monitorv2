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
    """Generate looking around robot eye animation with smooth saccades and scanning at 20 FPS (60 frames / 3.0s loop)."""
    frames = []
    total_frames = 60

    for i in range(total_frames):
        img, draw = new_frame()

        # Keyframe schedule:
        # 0..10: Glide center (0,0) -> left (-11,0)
        # 10..18: Hold gaze left (-11,0)
        # 18..30: Pan across left (-11,0) -> right (+11,0)
        # 30..38: Hold gaze right (+11,0)
        # 38..46: Glide right (+11,0) -> up (0,-5)
        # 46..54: Look up (0,-5) with clean blink in middle (49..52)
        # 54..60: Return up (0,-5) -> center (0,0)

        is_blinking = False
        blink_stage = 0

        if i < 10:
            t = ease_in_out(i / 10.0)
            dx = int(round(lerp(0, -11, t)))
            dy = 0
        elif i < 18:
            dx, dy = -11, 0
        elif i < 30:
            t = ease_in_out((i - 18) / 12.0)
            dx = int(round(lerp(-11, 11, t)))
            dy = 0
        elif i < 38:
            dx, dy = 11, 0
        elif i < 46:
            t = ease_in_out((i - 38) / 8.0)
            dx = int(round(lerp(11, 0, t)))
            dy = int(round(lerp(0, -5, t)))
        elif i < 54:
            dx, dy = 0, -5
            if 48 <= i <= 52:
                is_blinking = True
                blink_stage = i - 48
        else:
            t = ease_in_out((i - 54) / 6.0)
            dx = 0
            dy = int(round(lerp(-5, 0, t)))

        left_b = offset_box(DEFAULT_LEFT_BOX, dx=dx, dy=dy)
        right_b = offset_box(DEFAULT_RIGHT_BOX, dx=dx, dy=dy)

        if is_blinking:
            if blink_stage in (0, 4):
                # Half lid
                draw_squircle_eye(draw, scale_box(left_b, dh=-14))
                draw_squircle_eye(draw, scale_box(right_b, dh=-14))
            else:
                # Closed slit
                draw_slit_eye(draw, left_b, height=5)
                draw_slit_eye(draw, right_b, height=5)
        else:
            draw_squircle_eye(draw, left_b)
            draw_squircle_eye(draw, right_b)

        frames.append(img)

    return frames