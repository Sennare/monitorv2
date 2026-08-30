# lcd_core.py
import time
import threading
import digitalio
from PIL import Image, ImageDraw, ImageFont

# Adafruit CircuitPython RGB Display
import adafruit_rgb_display.ili9341 as ili9341

class LCDCore:
    """
    Core Display Manager for ILI9341 SPI Display (240x320).
    Handles graphics drawing, text wrapping, and automated backlight power management.
    """
    def __init__(self, spi, cs_pin, dc_pin, rst_pin, bl_pin, width=240, height=320, timeout_seconds=10.0):
        self.width = width
        self.height = height
        self.timeout_seconds = timeout_seconds
        
        # Setup Backlight Pin
        self.bl_pin = digitalio.DigitalInOut(bl_pin)
        self.bl_pin.direction = digitalio.Direction.OUTPUT
        self.bl_pin.value = False  # Start with backlight OFF
        
        # Initialize Display Driver
        self.disp = ili9341.ILI9341(
            spi,
            rotation=0, # 0 = portrait (240x320). Adjust to 90/270 for landscape (320x240)
            cs=digitalio.DigitalInOut(cs_pin),
            dc=digitalio.DigitalInOut(dc_pin),
            rst=digitalio.DigitalInOut(rst_pin),
            baudrate=32000000,
        )

        # Create PIL Image buffer and Draw object
        # "RGB" mode is required by the adafruit display library
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
        # Turn backlight ON
        self.bl_pin.value = True
        
        # Cancel existing timer if it exists
        if self._backlight_timer is not None:
            self._backlight_timer.cancel()
            
        # Start a new countdown timer
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
        # Common path for DejaVu fonts on Raspberry Pi OS
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
            # Fallback to default PIL font if the specific TTF is missing
            return ImageFont.load_default()

    # ==========================================
    # High-Level API Methods
    # ==========================================

    def set_background_color(self, color):
        """
        Fills the entire screen with the specified color.
        :param color: Tuple (R, G, B) or string like 'black', 'red'.
        """
        self._trigger_activity()
        self.draw.rectangle((0, 0, self.width, self.height), fill=color)
        self._update_display()

    def write_rows(self, rows, **options):
        """
        Prints a list of strings on separate lines.
        :param rows: List of strings.
        :param options: bg_color, text_color, font_size, bold, italic, line_spacing
        """
        self._trigger_activity()
        
        bg_color = options.get("bg_color", (0, 0, 0))
        text_color = options.get("text_color", (255, 255, 255))
        font_size = options.get("font_size", 16)
        bold = options.get("bold", False)
        italic = options.get("italic", False)
        line_spacing = options.get("line_spacing", 4)
        
        # Fill background
        self.draw.rectangle((0, 0, self.width, self.height), fill=bg_color)
        
        font = self._get_font(size=font_size, bold=bold, italic=italic)
        
        y_cursor = 10
        for row in rows:
            # Draw text
            self.draw.text((10, y_cursor), row, font=font, fill=text_color)
            
            # Calculate next line Y position using text bounding box
            bbox = self.draw.textbbox((10, y_cursor), row, font=font)
            text_height = bbox[3] - bbox[1]
            y_cursor += text_height + line_spacing
            
        self._update_display()

    def write_text(self, text, **options):
        """
        Prints a single long string, automatically wrapping it to the next line.
        :param text: String to write and wrap.
        :param options: bg_color, text_color, font_size, padding
        """
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
        
        # Word wrap logic based on pixel width of the font
        for word in words:
            test_line = f"{current_line}{word} "
            bbox = self.draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]
            
            if test_width <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = f"{word} "
        lines.append(current_line)  # Add the last line
        
        # Draw the wrapped lines
        y_cursor = padding
        for line in lines:
            self.draw.text((padding, y_cursor), line, font=font, fill=text_color)
            bbox = self.draw.textbbox((0, 0), line, font=font)
            text_height = bbox[3] - bbox[1]
            y_cursor += text_height + 4 # 4px line spacing
            
        self._update_display()

    def draw_graph(self, points, title="Graph", x_label="X", y_label="Y"):
        """
        Draws a simple 2D line graph from a list of (x, y) coordinates.
        :param points: List of tuples (x, y)
        """
        self._trigger_activity()
        
        # Clear screen to black
        self.draw.rectangle((0, 0, self.width, self.height), fill=(0, 0, 0))
        
        font_title = self._get_font(size=16, bold=True)
        font_labels = self._get_font(size=12)
        
        # Define Chart Area Margins
        margin_left = 30
        margin_bottom = 30
        margin_top = 40
        margin_right = 10
        
        chart_w = self.width - margin_left - margin_right
        chart_h = self.height - margin_top - margin_bottom
        
        # Draw Title
        self.draw.text((margin_left, 10), title, font=font_title, fill=(255, 255, 0))
        
        # Draw Axes
        origin = (margin_left, self.height - margin_bottom)
        x_end = (self.width - margin_right, self.height - margin_bottom)
        y_end = (margin_left, margin_top)
        
        self.draw.line([origin, x_end], fill=(255, 255, 255), width=2) # X Axis
        self.draw.line([origin, y_end], fill=(255, 255, 255), width=2) # Y Axis
        
        # Draw Axis Labels
        self.draw.text((self.width // 2, self.height - 20), x_label, font=font_labels, fill=(200, 200, 200))
        # Y label (horizontal near the top left)
        self.draw.text((5, margin_top - 20), y_label, font=font_labels, fill=(200, 200, 200))
        
        if not points:
            self._update_display()
            return
            
        # Calculate scales mapping real values to pixel coordinates
        x_vals = [p[0] for p in points]
        y_vals = [p[1] for p in points]
        
        min_x, max_x = min(x_vals), max(x_vals)
        min_y, max_y = min(y_vals), max(y_vals)
        
        range_x = (max_x - min_x) if max_x != min_x else 1
        range_y = (max_y - min_y) if max_y != min_y else 1
        
        # Translate points to screen coordinates
        screen_points = []
        for x, y in points:
            px = margin_left + ((x - min_x) / range_x) * chart_w
            # Y is inverted on screens (0 is at top)
            py = (self.height - margin_bottom) - ((y - min_y) / range_y) * chart_h
            screen_points.append((px, py))
            
        # Draw the line graph
        if len(screen_points) > 1:
            self.draw.line(screen_points, fill=(0, 255, 255), width=2)
            
        # Draw data points as little circles
        for px, py in screen_points:
            r = 2
            self.draw.ellipse((px-r, py-r, px+r, py+r), fill=(255, 0, 0))
            
        self._update_display()