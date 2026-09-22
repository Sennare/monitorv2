from PIL import Image, ImageDraw
from display.animations.lcd_animation import LcdAnimation

class CuteCatBlinkAnimation(LcdAnimation):
    """
    Animazione: Un gattino paffuto che sbatte le palpebre e sorride, 
    con bollicine fluttuanti sullo sfondo. Nessun testo.
    """
    def __init__(self, width=240, height=320):
        super().__init__()
        
        # Sfondo verde menta pastello
        bg_color = (170, 230, 200)
        cat_color = (255, 255, 255)       # Bianco
        blush_color = (255, 180, 190)     # Rosa per le guance
        eye_color = (40, 40, 40)          # Grigio scuro per occhi e bocca
        
        # Creiamo un loop di 4 frame
        for i in range(4):
            img = Image.new("RGB", (width, height), bg_color)
            draw = ImageDraw.Draw(img)
            
            # --- Disegno Orecchie (Triangoli) ---
            # Orecchio sinistro
            draw.polygon([(60, 90), (100, 150), (40, 150)], fill=cat_color)
            # Orecchio destro
            draw.polygon([(180, 90), (200, 150), (140, 150)], fill=cat_color)
            
            # --- Disegno Testa (Un grande ovale) ---
            draw.ellipse((40, 120, 200, 260), fill=cat_color)
            
            # --- Guance (Ovali rosa) ---
            draw.ellipse((55, 185, 85, 205), fill=blush_color)
            draw.ellipse((155, 185, 185, 205), fill=blush_color)
            
            # --- Bocca (Forma a 'w' carina con due archetti) ---
            # draw.arc(box, start, end, fill, width)
            draw.arc((105, 185, 120, 195), 0, 180, fill=eye_color, width=3)
            draw.arc((120, 185, 135, 195), 0, 180, fill=eye_color, width=3)
            
            # --- Occhi e Animazione Blink (sbattito di palpebre) ---
            if i == 1:
                # Nel frame 1 chiude gli occhi felice (archetti verso l'alto)
                draw.arc((70, 165, 95, 175), 180, 360, fill=eye_color, width=4)
                draw.arc((145, 165, 170, 175), 180, 360, fill=eye_color, width=4)
            else:
                # Negli altri frame tiene gli occhi aperti (ovali grandi)
                draw.ellipse((75, 160, 90, 180), fill=eye_color)
                draw.ellipse((150, 160, 165, 180), fill=eye_color)
                # Piccoli riflessi di luce per rendere gli occhi più "vivi"
                draw.ellipse((80, 162, 86, 168), fill=(255, 255, 255))
                draw.ellipse((155, 162, 161, 168), fill=(255, 255, 255))
            
            # --- Animazione Bollicine Fluttuanti ---
            # Spostiamo in verticale le bollicine in base al frame per farle fluttuare
            offset_y1 = (i * 8) % 24 
            offset_y2 = (i * 5) % 15
            
            # Bollicina gialla a sinistra
            draw.ellipse((30, 70 - offset_y1, 45, 85 - offset_y1), fill=(255, 230, 100))
            # Bollicina lilla a destra
            draw.ellipse((190, 50 + offset_y2, 200, 60 + offset_y2), fill=(200, 150, 255))
            
            self.frames.append(img)