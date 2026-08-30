# lcd_core.py
import time
import threading
import digitalio
import board
import busio
from PIL import Image, ImageDraw, ImageFont

# Adafruit CircuitPython RGB Display
import adafruit_rgb_display.ili9341 as ili9341


class LCDCore:
    """
    Core Display Manager for ILI9341 SPI Display (240x320).
    Handles graphics drawing, text wrapping, animations and automated backlight power management.
    """
    def __init__(self, spi=None, cs_pin=None, dc_pin=None, rst_pin=None, bl_pin=None, width=240, height=320, timeout_seconds=10.0):
        self.width = width
        self.height = height
        self.timeout_seconds = timeout_seconds
        
        # Inizializzazione standard senza parametri
        if spi is None:
            spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        cs_pin = cs_pin or board.D8
        dc_pin = dc_pin or board.D24
        rst_pin = rst_pin or board.D13
        bl_pin = bl_pin or board.D6
        
        # Setup Backlight Pin
        self.bl_pin = digitalio.DigitalInOut(bl_pin)
        self.bl_pin.direction = digitalio.Direction.OUTPUT
        self.bl_pin.value = False  # Start with backlight OFF
        
        # Initialize Display Driver
        self.disp = ili9341.ILI9341(
            spi,
            rotation=0, # 0 = portrait (240x320)
            cs=digitalio.DigitalInOut(cs_pin),
            dc=digitalio.DigitalInOut(dc_pin),
            rst=digitalio.DigitalInOut(rst_pin),
            baudrate=32000000,
        )

        self.image = Image.new("RGB", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        
        # Clear screen to black initially
        self.draw.rectangle((0, 0, self.width, self.height), fill=(0, 0, 0))
        self.disp.image(self.image)

        # Timer state
        self._backlight_timer = None

    # ==========================================
    # Power & Backlight Management
    # ==========================================
    
    def _turn_off_backlight(self):
        """Turns off the LCD backlight. Called by the inactivity timer."""
        self.bl_pin.value = False

    def _trigger_activity(self):
        """
        Wakes up the display (turns on backlight) and resets the inactivity timer.
        Must be called at the beginning of any drawing/writing method.
        """
        self.bl_pin.value = True
        
        if self._backlight_timer is not None:
            self._backlight_timer.cancel()
            
        self._backlight_timer = threading.Timer(self.timeout_seconds, self._turn_off_backlight)
        self._backlight_timer.start()

    def _update_display(self):
        """Pushes the current PIL image buffer to the physical SPI display."""
        self.disp.image(self.image)

    # ==========================================
    # Font Management Helper
    # ==========================================
    
    def _get_font(self, size=16, bold=False, italic=False):
        """Helper to load fonts. Defaults to standard Linux/Raspberry Pi paths."""
        base_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
        
        if bold and italic:
            font_path = f"{base_path}-BoldOblique.ttf"
        elif bold:
            font_path = f"{base_path}-Bold.ttf"
        elif italic:
            font_path = f"{base_path}-Oblique.ttf"
        else:
            font_path = f"{base_path}.ttf"
            
        try:
            return ImageFont.truetype(font_path, size)
        except IOError:
            return ImageFont.load_default()

    # ==========================================
    # High-Level API Methods
    # ==========================================

    def play_animation(self, animation, frame_delay=0.3, cycles=3):
        """
        Riproduce un'animazione sullo schermo.
        Mantiene acceso il backlight e fa partire il timeout solo alla fine.
        """
        # Accendiamo il display senza far partire il timer di timeout
        self.bl_pin.value = True
        if self._backlight_timer is not None:
            self._backlight_timer.cancel()
            
        frames = animation.get_frames()
        
        if not frames:
            return

        # Renderizziamo l'animazione
        for _ in range(cycles):
            for frame in frames:
                self.image.paste(frame)
                self._update_display()
                time.sleep(frame_delay)
                
        # Alla fine dell'animazione, attiviamo il timer per lo spegnimento
        self._trigger_activity()

    def set_background_color(self, color):
        """Fills the entire screen with the specified color."""
        self._trigger_activity()
        self.draw.rectangle((0, 0, self.width, self.height), fill=color)
        self._update_display()

    def write_rows(self, rows, **options):
        # [Codice originale invariato qui]
        self._trigger_activity()
        bg_color = options.get("bg_color", (0, 0, 0))
        text_color = options.get("text_color", (255, 255, 255))
        font_size = options.get("font_size", 16)
        bold = options.get("bold", False)
        italic = options.get("italic", False)
        line_spacing = options.get("line_spacing", 4)
        self.draw.rectangle((0, 0, self.width, self.height), fill=bg_color)
        font = self._get_font(size=font_size, bold=bold, italic=italic)
        y_cursor = 10
        for row in rows:
            self.draw.text((10, y_cursor), row, font=font, fill=text_color)
            bbox = self.draw.textbbox((10, y_cursor), row, font=font)
            text_height = bbox[3] - bbox[1]
            y_cursor += text_height + line_spacing
        self._update_display()

    def write_text(self, text, **options):
        # [Codice originale invariato qui]
        self._trigger_activity()
        bg_color = options.get("bg_color", (0, 0, 0))
        text_color = options.get("text_color", (255, 255, 255))
        font_size = options.get("font_size", 16)
        padding = options.get("padding", 10)
        self.draw.rectangle((0, 0, self.width, self.height), fill=bg_color)
        font = self._get_font(size=font_size)
        max_width = self.width - (padding * 2)
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line}{word} "
            bbox = self.draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]
            if test_width <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = f"{word} "
        lines.append(current_line)
        y_cursor = padding
        for line in lines:
            self.draw.text((padding, y_cursor), line, font=font, fill=text_color)
            bbox = self.draw.textbbox((0, 0), line, font=font)
            text_height = bbox[3] - bbox[1]
            y_cursor += text_height + 4
        self._update_display()
        
    def draw_graph(self, points, title="Graph", x_label="X", y_label="Y"):
        # [Codice originale invariato]
        pass # Rimosso per brevità, mantieni il tuo originale