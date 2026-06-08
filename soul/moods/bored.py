from PIL import Image, ImageDraw
from typing import List


def get_frames() -> List[Image.Image]:
    frames = []
    mouth_offset = [
        0,
        2,
        0,
        -2
    ]
    for i in range(4):
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        draw.line((32, 24, 48, 24), fill="white", width=3)
        draw.line((80, 24, 96, 24), fill="white", width=3)
        # mouth droop slightly every other frame
        draw.line((58, 46 + mouth_offset[i], 70, 44 + mouth_offset[i]), fill="white", width=2)
        frames.append(image)
    return frames
