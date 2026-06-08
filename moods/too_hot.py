from PIL import Image, ImageDraw
from typing import List


def get_frames() -> List[Image.Image]:
    frames = []
    for i in range(4):
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        draw.arc((32, 18, 48, 34), start=0, end=180, fill="white", width=2)
        draw.arc((80, 18, 96, 34), start=0, end=180, fill="white", width=2)
        draw.ellipse((54, 42, 74, 56), outline="white", width=2)
        # animate sweat droplet position
        if i % 2 == 0:
            draw.ellipse((20, 22, 24, 28), fill="white")
        else:
            draw.ellipse((22, 20, 26, 26), fill="white")
        draw.line([(22, 17), (22, 23)], fill="white", width=1)
        frames.append(image)
    return frames
