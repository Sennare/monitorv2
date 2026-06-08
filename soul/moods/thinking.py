from PIL import Image, ImageDraw
from typing import List


def get_frames() -> List[Image.Image]:
    frames = []
    for i in range(4):
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        draw.ellipse((38, 14, 48, 24), fill="white")
        draw.ellipse((86, 14, 96, 24), fill="white")
        draw.line((58, 46, 68, 46), fill="white", width=2)
        # floating dots animate position
        if i == 0:
            draw.ellipse((104, 20, 106, 22), fill="white")
        elif i == 1:
            draw.ellipse((108, 16, 110, 18), fill="white")
        elif i == 2:
            draw.ellipse((110, 12, 114, 16), fill="white")
        else:
            draw.ellipse((106, 14, 108, 16), fill="white")
        frames.append(image)
    return frames
