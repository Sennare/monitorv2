from PIL import Image, ImageDraw
from typing import List


def get_frames() -> List[Image.Image]:
    frames = []
    for i in range(4):
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        # drooping eyes; animate a small tear on frame 3
        draw.arc((32, 16, 48, 32), start=0, end=180, fill="white", width=3)
        draw.arc((80, 16, 96, 32), start=0, end=180, fill="white", width=3)
        draw.arc((54, 46, 74, 58), start=180, end=0, fill="white", width=2)
        if i == 2:
            draw.ellipse((46, 34, 50, 38), fill="white")
        frames.append(image)
    return frames
