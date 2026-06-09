from PIL import Image, ImageDraw
from typing import List


def get_frames() -> List[Image.Image]:
    frames = []
    for i in range(4):
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        
        # Bocca semplice e fissa al centro
        draw.line((58, 46, 68, 46), fill="white", width=2)
        
        if i == 0:
            # Frame 0: Guarda a SINISTRA (coordinate X traslate a sinistra di 4 pixel)
            draw.ellipse((34, 14, 44, 24), fill="white")
            draw.ellipse((82, 14, 92, 24), fill="white")
        elif i == 2:
            # Frame 2: Guarda a DESTRA (coordinate X traslate a destra di 4 pixel)
            draw.ellipse((42, 14, 52, 24), fill="white")
            draw.ellipse((90, 14, 100, 24), fill="white")
        else:
            # Frame 1 e 3: Guarda al CENTRO (posizione di partenza)
            draw.ellipse((38, 14, 48, 24), fill="white")
            draw.ellipse((86, 14, 96, 24), fill="white")
            
        frames.append(image)
    return frames