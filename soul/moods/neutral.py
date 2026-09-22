import math
from typing import List
from PIL import Image
from soul.moods.robot_eyes import (
    new_frame,
    draw_squircle_eye,
    draw_slit_eye,
    scale_box,
    DEFAULT_LEFT_BOX,
    DEFAULT_RIGHT_BOX,
)


def get_frames() -> List[Image.Image]:
    """Generate neutral robot eye frames with natural blinking and idle gaze at 20 FPS (50 frames / 2.5s loop)."""
    frames = []
    total_frames = 50

    for i in range(total_frames):
        img, draw = new_frame()

        if 36 <= i <= 44:
            # Smooth 9-frame blink sequence (~0.45s)
            blink_phase = i - 36
            if blink_phase == 0:
                dh = -6
                draw_squircle_eye(draw, scale_box(DEFAULT_LEFT_BOX, dh=dh))
                draw_squircle_eye(draw, scale_box(DEFAULT_RIGHT_BOX, dh=dh))
            elif blink_phase == 1:
                dh = -14
                draw_squircle_eye(draw, scale_box(DEFAULT_LEFT_BOX, dh=dh))
                draw_squircle_eye(draw, scale_box(DEFAULT_RIGHT_BOX, dh=dh))
            elif blink_phase == 2:
                dh = -22
                draw_squircle_eye(draw, scale_box(DEFAULT_LEFT_BOX, dh=dh))
                draw_squircle_eye(draw, scale_box(DEFAULT_RIGHT_BOX, dh=dh))
            elif blink_phase == 3:
                draw_slit_eye(draw, DEFAULT_LEFT_BOX, height=6)
                draw_slit_eye(draw, DEFAULT_RIGHT_BOX, height=6)
            elif blink_phase == 4:
                draw_slit_eye(draw, DEFAULT_LEFT_BOX, height=5)
                draw_slit_eye(draw, DEFAULT_RIGHT_BOX, height=5)
            elif blink_phase == 5:
                dh = -20
                draw_squircle_eye(draw, scale_box(DEFAULT_LEFT_BOX, dh=dh))
                draw_squircle_eye(draw, scale_box(DEFAULT_RIGHT_BOX, dh=dh))
            elif blink_phase == 6:
                dh = -12
                draw_squircle_eye(draw, scale_box(DEFAULT_LEFT_BOX, dh=dh))
                draw_squircle_eye(draw, scale_box(DEFAULT_RIGHT_BOX, dh=dh))
            elif blink_phase == 7:
                dh = -4
                draw_squircle_eye(draw, scale_box(DEFAULT_LEFT_BOX, dh=dh))
                draw_squircle_eye(draw, scale_box(DEFAULT_RIGHT_BOX, dh=dh))
            else:  # blink_phase == 8 (elastic settle)
                dh = 1
                draw_squircle_eye(draw, scale_box(DEFAULT_LEFT_BOX, dh=dh))
                draw_squircle_eye(draw, scale_box(DEFAULT_RIGHT_BOX, dh=dh))
        else:
            # Idle resting gaze with subtle robotic micro-breathing (sub-pixel oscillation)
            breathe = int(round(math.sin(i / total_frames * 2 * math.pi) * 1.0))
            left_box = scale_box(DEFAULT_LEFT_BOX, dh=breathe)
            right_box = scale_box(DEFAULT_RIGHT_BOX, dh=breathe)
            draw_squircle_eye(draw, left_box)
            draw_squircle_eye(draw, right_box)

        frames.append(img)

    return frames