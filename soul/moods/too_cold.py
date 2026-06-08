from PIL import Image, ImageDraw
from typing import List


def get_frames() -> List[Image.Image]:
    frames = []
    for i in range(4):
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        # shivering lines; alternate zig-zag offset
        offset = 0 if i % 2 == 0 else 1
        draw.line([(34 + offset, 20), (44 + offset, 24), (34 + offset, 28)], fill="white", width=2)
        draw.line([(94 - offset, 20), (84 - offset, 24), (94 - offset, 28)], fill="white", width=2)
        draw.line([(52, 46), (57, 51), (62, 46), (67, 51), (72, 46), (77, 51)], fill="white", width=2)
        frames.append(image)
    return frames
