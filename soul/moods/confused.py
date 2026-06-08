from PIL import Image, ImageDraw
from typing import List


def get_frames() -> List[Image.Image]:
    frames = []
    for i in range(4):
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        # left X eye
        draw.line((34, 18, 46, 30), fill="white", width=2)
        draw.line((46, 18, 34, 30), fill="white", width=2)
        draw.ellipse((82, 18, 94, 30), fill="white")
        # wiggle mouth between frames
        if i % 2 == 0:
            draw.line((54, 48, 64, 42), fill="white", width=2)
            draw.line((64, 42, 74, 48), fill="white", width=2)
        else:
            draw.line((54, 46, 64, 40), fill="white", width=2)
            draw.line((64, 40, 74, 46), fill="white", width=2)
        frames.append(image)
    return frames
