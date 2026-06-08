from PIL import Image, ImageDraw
from typing import List


def get_frames() -> List[Image.Image]:
    frames = []
    for i in range(4):
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        # blink on frame 2
        if i == 2:
            draw.line((34, 24, 46, 24), fill="white", width=2)
            draw.line((82, 24, 94, 24), fill="white", width=2)
        else:
            draw.ellipse((34, 18, 46, 30), fill="white")
            draw.ellipse((82, 18, 94, 30), fill="white")
        draw.line((56, 46, 72, 46), fill="white", width=2)
        frames.append(image)
    return frames
