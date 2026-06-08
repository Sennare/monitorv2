from PIL import Image, ImageDraw
from typing import List


def get_frames() -> List[Image.Image]:
    frames = []
    for i in range(4):
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        draw.ellipse((34, 22, 46, 34), fill="white")
        draw.ellipse((82, 22, 94, 34), fill="white")
        draw.line((30, 14, 48, 20), fill="white", width=2)
        draw.line((98, 14, 80, 20), fill="white", width=2)
        draw.line((58, 48, 70, 48), fill="white", width=2)
        frames.append(image)
    return frames
