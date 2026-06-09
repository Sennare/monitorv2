from PIL import Image, ImageDraw
from typing import List

def get_frames() -> List[Image.Image]:
    frames = []
    for i in range(8):
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        s = 20
        pupil_xoffset_frames = [0,0,0,0,0,3,-3,0]
        pupil_yoffset_frames = [0,0,0,0,0,-3,-3,0]
        pupil_sizeoffset_frames = [0,0,0,-4,0,0,0,0]
        # blink on frame 2
        if i == 2:
            draw.line((34, 24, 46, 24), fill="white", width=2)
            draw.line((82, 24, 94, 24), fill="white", width=2)
        else:
            # Bigger eye
            o_x = pupil_xoffset_frames[i] #2 if i == 6 else (-2 if i == 7 else 0)
            o_y = pupil_yoffset_frames[i] # -2 if i == 6 else (-2 if i == 7 else 0)
            o_s = pupil_sizeoffset_frames[i]
            draw.ellipse(build_cords(40+o_x, 24+o_y, s+o_s), fill="white")
            draw.ellipse(build_cords(88+o_x, 24+o_y, s+o_s), fill="white")
            # Pupil
            #draw.ellipse(build_cords(40+o_x, 24+o_y, 10+o_s), fill="black")
            #draw.ellipse(build_cords(88+o_x, 24+o_y, 10+o_s), fill="black")

        # curva principale
        draw.arc(build_cords_wh(64,50,28,6), 0, 180, fill="white", width=2)

        draw.arc(build_cords_wh(40,47,25,20), -10, 50, fill="white", width=2)
        draw.arc(build_cords_wh(90,47,25,20), 130, 190, fill="white", width=2)

        #draw.line((56, 46, 72, 46), fill="white", width=2)
        frames.append(image)
    return frames

def build_cords(x, y, s):
    return (
            x - (s/2), 
            y - (s/2), 
            x + (s/2), 
            y + (s/2))

def build_cords_wh(x, y, w, h):
    return (
            x - (w/2), 
            y - (h/2), 
            x + (w/2), 
            y + (h/2))