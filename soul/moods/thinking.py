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
    """Generate thinking robot eyes looking up-right with cycling digital processing blocks."""
    frames = []

    for i in range(4):
        img, draw = new_frame()

        # Eyes shifted up and to the right in contemplation
        scan_x = 5 + (1 if i in (1, 2) else 0)
        left_b = offset_box(scale_box(DEFAULT_LEFT_BOX, dh=-2), dx=scan_x, dy=-5)
        right_b = offset_box(scale_box(DEFAULT_RIGHT_BOX, dh=-2), dx=scan_x, dy=-5)

        draw_squircle_eye(draw, left_b)
        draw_squircle_eye(draw, right_b)

        # Digital loading/processing indicator dots in top right
        dot_xs = [104, 112, 120]
        dot_y = 10
        for d_idx, x in enumerate(dot_xs):
            is_active = (d_idx == i) or (i == 3)
            if is_active:
                draw.rectangle((x, dot_y, x + 4, dot_y + 4), fill="white")
            else:
                draw.rectangle((x, dot_y, x + 4, dot_y + 4), outline="white", width=1)

        frames.append(img)

    return frames
