from PIL import Image, ImageDraw
from typing import List

# Helper per disegnare l'occhio con la scintilla
def draw_sparkle_eye(draw, coords, sparkle_pattern=1):
    x, y, r = coords
    draw.ellipse((x-r, y-r, x+r, y+r), fill="white")
    if sparkle_pattern == 1:
        # Scintilla standard
        draw.point([(x-2, y-2), (x-3, y-3), (x+3, y-3)], fill="black")
    elif sparkle_pattern == 2:
        # Scintilla Hyper-Cute
        draw.point([(x+1, y+1), (x+2, y+2), (x-2, y-2)], fill="black")

def get_frames() -> List[Image.Image]:
    frames = []
    
    # Parametri costanti
    w, h = 128, 64
    r_center = (h // 2) - 10  # Posizione verticale degli occhi
    r_dist = 22 # Distanza dal centro per ciascun occhio
    eye_radius = 16  # Occhi resi GIGANTI

    for i in range(8):
        image = Image.new("1", (w, h))
        draw = ImageDraw.Draw(image)
        
        # Bocca 'w' fissa
        draw.line([(58, 52), (61, 55), (64, 52), (67, 55), (70, 52)], fill="white", width=2)
        # Rossore fisso
        draw.point([(36, 42), (88, 42)], fill="white")

        #--- Logica dei 8 Stati Unici ---
        if i == 0:
            # Stato 1: Cute Base
            draw_sparkle_eye(draw, (w//2-r_dist, r_center, eye_radius))
            draw_sparkle_eye(draw, (w//2+r_dist, r_center, eye_radius))
        elif i == 1:
            # Stato 2: Sguardo Sinistro
            draw_sparkle_eye(draw, (w//2-r_dist-6, r_center, eye_radius))
            draw_sparkle_eye(draw, (w//2+r_dist-6, r_center, eye_radius))
        elif i == 2:
            # Stato 3: Sguardo Destro
            draw_sparkle_eye(draw, (w//2-r_dist+6, r_center, eye_radius))
            draw_sparkle_eye(draw, (w//2+r_dist+6, r_center, eye_radius))
        elif i == 3:
            # Stato 4: Sguardo in Alto
            draw_sparkle_eye(draw, (w//2-r_dist, r_center-6, eye_radius))
            draw_sparkle_eye(draw, (w//2+r_dist, r_center-6, eye_radius))
        elif i == 4:
            # Stato 5: uwu Squint
            draw.chord((w//2-r_dist-eye_radius, r_center-eye_radius//2, w//2-r_dist+eye_radius, r_center+eye_radius//2), start=180, end=0, fill="white")
            draw.chord((w//2+r_dist-eye_radius, r_center-eye_radius//2, w//2+r_dist+eye_radius, r_center+eye_radius//2), start=180, end=0, fill="white")
        elif i == 5:
            # Stato 6: Occhi Chiusi (Smiling)
            draw.arc((w//2-r_dist-eye_radius, r_center-eye_radius//2, w//2-r_dist+eye_radius, r_center+eye_radius//2), start=180, end=0, fill="white", width=2)
            draw.arc((w//2+r_dist-eye_radius, r_center-eye_radius//2, w//2+r_dist+eye_radius, r_center+eye_radius//2), start=180, end=0, fill="white", width=2)
        elif i == 6:
            # Stato 7: Wink & Curiosità
            # Occhio sinistro wink
            draw.arc((w//2-r_dist-eye_radius, r_center-eye_radius//2, w//2-r_dist+eye_radius, r_center+eye_radius//2), start=180, end=0, fill="white", width=2)
            # Occhio destro aperto
            draw_sparkle_eye(draw, (w//2+r_dist, r_center, eye_radius))
            # Punto di domanda
            draw.point([(w//2+r_dist+20, r_center-10)], fill="white")
        elif i == 7:
            # Stato 8: Hyper-Cute Sparkle
            # Occhi ancora più rotondi e scintilla differente
            draw_sparkle_eye(draw, (w//2-r_dist, r_center, eye_radius+2), sparkle_pattern=2)
            draw_sparkle_eye(draw, (w//2+r_dist, r_center, eye_radius+2), sparkle_pattern=2)
        
        frames.append(image)
    return frames