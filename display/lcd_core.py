# lcd_core.py
import os
import time
import threading
from PIL import Image, ImageDraw, ImageFont

# Optional hardware imports with graceful fallback for testing/off-Pi development
try:
    import board
    import busio
    import digitalio
    import adafruit_rgb_display.ili9341 as ili9341
    HARDWARE_AVAILABLE = True
except (ImportError, NotImplementedError):
    board = None
    busio = None
    digitalio = None
    ili9341 = None
    HARDWARE_AVAILABLE = False


class _MockPin:
    def __init__(self):
        self.value = False
        self.direction = None


class _MockDisplay:
    def __init__(self, width=240, height=320):
        self.width = width
        self.height = height

    def image(self, img):
        pass


class LCDCore:
    """
    Core Display Manager for ILI9341 SPI Display (240x320 portrait).
    Handles graphics drawing, animations, thread synchronization,
    and automated 45-second inactivity backlight power management.
    """
    _instance = None
    _singleton_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super(LCDCore, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(
        self,
        spi=None,
        cs_pin=None,
        dc_pin=None,
        rst_pin=None,
        bl_pin=None,
        width=240,
        height=320,
        timeout_seconds=45.0,
    ):
        if getattr(self, "_initialized", False):
            return

        self.width = width
        self.height = height
        self.timeout_seconds = timeout_seconds

        # Concurrency & rendering locks
        self._disp_lock = threading.RLock()
        self._anim_lock = threading.RLock()
        self._anim_stop_event = threading.Event()
        self._anim_thread = None

        # Backlight & power state
        self._backlight_timer = None
        self.is_screen_on = False
        self.on_inactivity_timeout = None
        self.brightness = 100  # Default 100%
        self._pwm = None

        if HARDWARE_AVAILABLE and board is not None:
            # Pin mapping: RST = GPIO 13 (Pin 33), BL = GPIO 6 (Pin 31)
            # Supports optional environment variable overrides for custom bench wiring
            env_rst = os.environ.get("LCD_RST_PIN")
            env_bl = os.environ.get("LCD_BL_PIN")
            rst_num = int(env_rst) if env_rst else 13
            bl_num = int(env_bl) if env_bl else 6

            rst_pin = rst_pin or getattr(board, f"D{rst_num}", board.D13)
            bl_pin = bl_pin or getattr(board, f"D{bl_num}", board.D6)
            cs_pin = cs_pin or board.D8
            dc_pin = dc_pin or board.D24

            # 1. Initialize Display SPI Controller independently
            # Hardware reset pin is strictly dedicated to ILI9341 and NEVER pulsed by PWM
            try:
                if spi is None:
                    spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI, MISO=board.MISO)

                self.disp = ili9341.ILI9341(
                    spi,
                    rotation=0,  # portrait 240x320
                    cs=digitalio.DigitalInOut(cs_pin),
                    dc=digitalio.DigitalInOut(dc_pin),
                    rst=digitalio.DigitalInOut(rst_pin),
                    baudrate=64000000,
                )
                print(f"[lcd_core] Hardware ILI9341 SPI display initialized (CS={cs_pin}, DC={dc_pin}, RST={rst_pin}).")
            except Exception as e:
                print(f"[lcd_core] Hardware display init failed ({e}), using mock display.")
                self.disp = _MockDisplay(width, height)

            # 2. Initialize Backlight in a completely isolated block so it NEVER aborts display initialization
            try:
                self._init_backlight(bl_pin)
            except Exception as e:
                print(f"[lcd_core] Backlight setup error ({e}), using mock pin.")
                self.bl_pin = _MockPin()
        else:
            self.bl_pin = _MockPin()
            self.disp = _MockDisplay(width, height)

        self.image = Image.new("RGB", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

        # Initially clear display to black
        with self._disp_lock:
            self.draw.rectangle((0, 0, self.width, self.height), fill=(0, 0, 0))
            self.disp.image(self.image)

        self._initialized = True

    def _init_backlight(self, bl_pin):
        """
        Initializes backlight with software PWM brightness control if available,
        falling back to digital on/off.
        The backlight pin is strictly isolated and never touches the display reset line.
        """
        self._pwm = None
        self.bl_pin = None

        # 1. Try gpiozero software PWM for flexible brightness modulation (10%-100%)
        try:
            from gpiozero import PWMOutputDevice
            pin_num = getattr(bl_pin, "id", None)
            if not isinstance(pin_num, int):
                digits = "".join([c for c in str(bl_pin) if c.isdigit()])
                pin_num = int(digits) if digits else 6

            self._pwm = PWMOutputDevice(pin_num, frequency=200, initial_value=1.0)
            print(f"[lcd_core] Backlight initialized with gpiozero PWM on GPIO {pin_num}.")
        except Exception as e:
            self._pwm = None
            print(f"[lcd_core] PWM init not available ({e}), falling back to digital on/off.")

        # 2. Fallback to digital on/off via digitalio
        if self._pwm is None:
            try:
                self.bl_pin = digitalio.DigitalInOut(bl_pin)
                self.bl_pin.direction = digitalio.Direction.OUTPUT
                self.bl_pin.value = True
                print(f"[lcd_core] Backlight initialized with digital on/off on pin {bl_pin}.")
            except Exception as e:
                print(f"[lcd_core] Digital backlight pin setup failed ({e}), using mock pin.")
                self.bl_pin = _MockPin()

    # ==========================================
    # Power & Backlight Management (45s Inactivity & Brightness)
    # ==========================================

    @property
    def is_backlight_on(self) -> bool:
        return self.is_screen_on

    def _apply_backlight(self):
        """Applies current brightness and power state to physical backlight."""
        target_pct = self.brightness if self.is_screen_on else 0
        if self._pwm is not None:
            try:
                if hasattr(self._pwm, "duty_cycle"):
                    self._pwm.duty_cycle = int((target_pct / 100.0) * 65535)
                elif hasattr(self._pwm, "value"):
                    self._pwm.value = target_pct / 100.0
            except Exception as e:
                print(f"[lcd_core] Backlight PWM error: {e}")
        elif hasattr(self, "bl_pin") and self.bl_pin is not None:
            try:
                self.bl_pin.value = (target_pct > 0)
            except Exception:
                pass

    def set_brightness(self, level: int) -> int:
        """Sets backlight brightness percentage (10% to 100%)."""
        self.brightness = max(10, min(100, int(level)))
        self._apply_backlight()
        return self.brightness

    def get_brightness(self) -> int:
        """Gets current backlight brightness percentage."""
        return self.brightness

    def turn_off(self):
        """Puts the display to sleep: turns off backlight, stops animations, keeps LCD image."""
        self.stop_animation()
        self.is_screen_on = False
        self._apply_backlight()

        if self._backlight_timer is not None:
            self._backlight_timer.cancel()
            self._backlight_timer = None

    def turn_on(self):
        """Wakes up the display: turns on backlight and starts 45s inactivity timer."""
        self.is_screen_on = True
        self._apply_backlight()
        self.reset_inactivity_timer()

    def _on_inactivity_timeout_fired(self):
        """Callback executed when the inactivity timer elapses."""
        if self.on_inactivity_timeout is not None:
            try:
                self.on_inactivity_timeout()
                return
            except Exception as e:
                print(f"[lcd_core] Error in on_inactivity_timeout callback: {e}")
        self.turn_off()

    def reset_inactivity_timer(self):
        """Resets the 45-second inactivity timer."""
        if self._backlight_timer is not None:
            self._backlight_timer.cancel()

        self._backlight_timer = threading.Timer(self.timeout_seconds, self._on_inactivity_timeout_fired)
        self._backlight_timer.daemon = True
        self._backlight_timer.start()

    def _trigger_activity(self):
        """Called upon user interaction to reset inactivity timer if display is active."""
        if self.is_screen_on:
            self.reset_inactivity_timer()

    def _update_display(self):
        """Pushes the current PIL image buffer to the physical SPI display under lock."""
        try:
            self.disp.image(self.image)
        except Exception as e:
            print(f"[lcd_core] SPI display update error: {e}")

    # ==========================================
    # Font Management Helper
    # ==========================================

    def _get_font(self, size=16, bold=False, italic=False):
        """Helper to load fonts with fallback."""
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
    # Animation Control & Concurrency Safety
    # ==========================================

    def stop_animation(self, wait=True):
        """Signals any currently running animation thread to stop and waits for it."""
        with self._anim_lock:
            self._anim_stop_event.set()
            if wait and self._anim_thread is not None and self._anim_thread.is_alive():
                if threading.current_thread() != self._anim_thread:
                    self._anim_thread.join(timeout=1.0)
            self._anim_thread = None

    def _play_animation_frames(self, frames, frame_delay, cycles, on_complete=None):
        """Background worker thread: plays animation frames while checking stop_event."""
        try:
            for _ in range(cycles):
                for frame in frames:
                    if self._anim_stop_event.is_set():
                        return

                    with self._disp_lock:
                        self.image.paste(frame)
                        self._update_display()

                    # Sleep in small slices so stopping is immediate
                    sleep_remaining = frame_delay
                    while sleep_remaining > 0:
                        if self._anim_stop_event.is_set():
                            return
                        slice_time = min(0.05, sleep_remaining)
                        time.sleep(slice_time)
                        sleep_remaining -= slice_time

            if not self._anim_stop_event.is_set() and on_complete is not None:
                on_complete()
        finally:
            self._trigger_activity()

    def play_animation(self, animation, frame_delay=0.3, cycles=3, on_complete=None):
        """
        Plays an animation on the display in a dedicated thread.
        Cleanly cancels and stops any previous animation before starting.
        """
        self.stop_animation()

        # Wake up display
        self.turn_on()

        frames = animation.get_frames() if animation is not None else []
        if not frames:
            if on_complete:
                on_complete()
            return

        try:
            cycles = max(1, int(cycles))
        except (TypeError, ValueError):
            cycles = 1

        try:
            frame_delay = max(0.0, float(frame_delay))
        except (TypeError, ValueError):
            frame_delay = 0.3

        with self._anim_lock:
            self._anim_stop_event.clear()
            self._anim_thread = threading.Thread(
                target=self._play_animation_frames,
                args=(frames, frame_delay, cycles, on_complete),
                daemon=True,
            )
            self._anim_thread.start()

    # ==========================================
    # High-Level Page Rendering Primitives
    # ==========================================

    def render_image(self, img):
        """Directly paints an external PIL image to the display buffer."""
        self.stop_animation()
        with self._disp_lock:
            self.image.paste(img)
            self._update_display()

    def set_background_color(self, color):
        """Fills the entire screen with the specified color."""
        self.stop_animation()
        with self._disp_lock:
            self.draw.rectangle((0, 0, self.width, self.height), fill=color)
            self._update_display()

    def write_rows(self, rows, **options):
        """Prints a list of strings on separate lines with layout styling."""
        self.stop_animation()

        bg_color = options.get("bg_color", (0, 0, 0))
        text_color = options.get("text_color", (255, 255, 255))
        font_size = options.get("font_size", 16)
        bold = options.get("bold", False)
        italic = options.get("italic", False)
        line_spacing = options.get("line_spacing", 4)
        margin_y = options.get("margin_y", 10)
        margin_x = options.get("margin_x", 10)

        with self._disp_lock:
            self.draw.rectangle((0, 0, self.width, self.height), fill=bg_color)
            font = self._get_font(size=font_size, bold=bold, italic=italic)

            y_cursor = margin_y
            for row in rows:
                self.draw.text((margin_x, y_cursor), row, font=font, fill=text_color)
                bbox = self.draw.textbbox((margin_x, y_cursor), row, font=font)
                text_height = bbox[3] - bbox[1]
                y_cursor += text_height + line_spacing

            self._update_display()

    def write_text(self, text, **options):
        """Prints a single long string, automatically wrapping it to next line."""
        self.stop_animation()

        bg_color = options.get("bg_color", (0, 0, 0))
        text_color = options.get("text_color", (255, 255, 255))
        font_size = options.get("font_size", 16)
        padding = options.get("padding", 10)

        with self._disp_lock:
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