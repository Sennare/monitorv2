from PIL import Image, ImageDraw
from typing import List


def get_frames() -> List[Image.Image]:
    frames = []
    for i in range(4):
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        # eyes arc: make a tiny mouth wobble on frames
        draw.arc((32, 18, 48, 34), start=180, end=0, fill="white", width=3)
        draw.arc((80, 18, 96, 34), start=180, end=0, fill="white", width=3)
        mouth_offset = -1 if i % 2 == 0 else 1
        draw.chord((52, 40 + mouth_offset, 76, 56 + mouth_offset), start=0, end=180, fill="white")
        frames.append(image)
    return frames
