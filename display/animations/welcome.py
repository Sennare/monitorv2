from PIL import Image, ImageDraw, ImageFont
from display.animations.lcd_animation import LcdAnimation

class CuteCiaoAnimation(LcdAnimation):
    """
    Animazione Demo: Scritta "Ciao" cute con disegnini colorati e animati.
    """
    def __init__(self, width=240, height=320):
        super().__init__()
        
        # Generiamo 3 frame per l'animazione
        colors = [(255, 105, 180), (0, 255, 255), (255, 255, 0)] # Rosa, Ciano, Giallo
        
        # Cerchiamo di caricare un font decente, altrimenti fallback
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        except IOError:
            font_large = ImageFont.load_default()

        for i in range(3):
            # RGB mode è richiesto dalla libreria adafruit
            img = Image.new("RGB", (width, height), (30, 20, 50)) # Sfondo viola scuro
            draw = ImageDraw.Draw(img)
            
            # Colore dinamico in base al frame
            text_color = colors[i % len(colors)]
            deco_color_1 = colors[(i + 1) % len(colors)]
            deco_color_2 = colors[(i + 2) % len(colors)]
            
            # Scritta centrale "Ciao!" con un piccolo offset per simulare un "rimbalzo"
            y_offset = -5 if i == 1 else 0
            
            # Testo al centro (calcolo approssimativo)
            draw.text((70, 130 + y_offset), "Ciao!", font=font_large, fill=text_color)
            
            # Disegnini cute (cerchi/scintille che cambiano dimensione/posizione)
            r = 10 if i % 2 == 0 else 15
            
            # Cuoricini/Cerchietti in alto a sinistra e in basso a destra
            draw.ellipse((30, 50 + y_offset, 30+r, 50+r+y_offset), fill=deco_color_1)
            draw.ellipse((45, 40 + y_offset, 45+(r-5), 40+(r-5)+y_offset), fill=deco_color_1)
            
            draw.ellipse((180, 250 - y_offset, 180+r, 250+r-y_offset), fill=deco_color_2)
            draw.ellipse((165, 260 - y_offset, 165+(r-5), 260+(r-5)-y_offset), fill=deco_color_2)
            
            # Piccole stelline (croci)
            draw.text((200, 80), "+", font=font_large, fill=deco_color_2)
            draw.text((40, 220), "+", font=font_large, fill=deco_color_1)

            self.frames.append(img)