from PIL import Image, ImageDraw
from typing import List


def get_frames() -> List[Image.Image]:
    frames = []
    for i in range(4):
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        draw.ellipse((30, 14, 48, 32), fill="white")
        # wink every 3rd frame on the small eye
        if i == 2:
            draw.line((84, 24, 92, 24), fill="white", width=2)
        else:
            draw.ellipse((84, 20, 92, 28), fill="white")
        draw.ellipse((60, 42, 68, 50), outline="white", width=2)
        frames.append(image)
    return frames
