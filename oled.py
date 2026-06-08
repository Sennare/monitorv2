from luma.core.interface.serial import i2c
from luma.core.interface.parallel import bitbang_6800
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
from state import EventType, Mood, SetMood, StateStore

class OledDisplay:
    def __init__(self):
        serial = i2c(port=1, address=0x3C)
        self.device = ssd1306(serial, width=128, height=64, rotate=0)
        self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)

        self.state_store = StateStore()
        self.state_store.subscribe(EventType.MOOD_CHANGED.value, self._on_mood_changed)

    def _on_mood_changed(self, mood: Mood) -> None:
        # Create a blank 1-bit canvas image
        print(f"[oled] Mood changed to {mood.value}, updating display...")
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        
        match mood:
            case Mood.NEUTRAL:
                # Simple cute round eyes
                draw.ellipse((34, 18, 46, 30), fill="white")
                draw.ellipse((82, 18, 94, 30), fill="white")
                # Straight little mouth
                draw.line((56, 46, 72, 46), fill="white", width=2)

            case Mood.HAPPY:
                # Happy upward arcs for eyes (^ ^)
                draw.arc((32, 18, 48, 34), start=180, end=0, fill="white", width=3)
                draw.arc((80, 18, 96, 34), start=180, end=0, fill="white", width=3)
                # Big open-mouth smile
                draw.chord((52, 40, 76, 56), start=0, end=180, fill="white")

            case Mood.SAD:
                # Drooping sad eyes
                draw.arc((32, 16, 48, 32), start=0, end=180, fill="white", width=3)
                draw.arc((80, 16, 96, 32), start=0, end=180, fill="white", width=3)
                # Downward arc frown
                draw.arc((54, 46, 74, 58), start=180, end=0, fill="white", width=2)

            case Mood.ANGRY:
                # Round eyes with angry slanted eyebrows over them (> < style angle)
                draw.ellipse((34, 22, 46, 34), fill="white")
                draw.ellipse((82, 22, 94, 34), fill="white")
                draw.line((30, 14, 48, 20), fill="white", width=2) # Left brow
                draw.line((98, 14, 80, 20), fill="white", width=2) # Right brow
                # Flat, displeased mouth
                draw.line((58, 48, 70, 48), fill="white", width=2)

            case Mood.CURIOUS:
                # One wide open eye, one regular eye
                draw.ellipse((30, 14, 48, 32), fill="white")
                draw.ellipse((84, 20, 92, 28), fill="white")
                # Small cute "o" mouth
                draw.ellipse((60, 42, 68, 50), outline="white", width=2)

            case Mood.CONFUSED:
                # Asymmetric eyes: an 'X' left eye and an 'O' right eye
                draw.line((34, 18, 46, 30), fill="white", width=2)
                draw.line((46, 18, 34, 30), fill="white", width=2)
                draw.ellipse((82, 18, 94, 30), fill="white")
                # Wavy zig-zag mouth line
                draw.line((54, 48, 64, 42), fill="white", width=2)
                draw.line((64, 42, 74, 48), fill="white", width=2)

            case Mood.THINKING:
                # Eyes looking upward and to the right corner
                draw.ellipse((38, 14, 48, 24), fill="white")
                draw.ellipse((86, 14, 96, 24), fill="white")
                # Subdued side-smirk mouth
                draw.line((58, 46, 68, 46), fill="white", width=2)
                # Tiny floating thinking dots on the top right
                draw.ellipse((104, 20, 106, 22), fill="white")
                draw.ellipse((110, 12, 114, 16), fill="white")

            case Mood.TOO_COLD:
                # Tightly shut shivering eyes (> < style)
                draw.line([(34, 20), (44, 24), (34, 28)], fill="white", width=2)
                draw.line([(94, 20), (84, 24), (94, 28)], fill="white", width=2)
                # Shivering/chattering zig-zag mouth line
                draw.line([(52, 46), (57, 51), (62, 46), (67, 51), (72, 46), (77, 51)], fill="white", width=2)

            case Mood.TOO_HOT:
                # Exhausted, melting downward arc eyes
                draw.arc((32, 18, 48, 34), start=0, end=180, fill="white", width=2)
                draw.arc((80, 18, 96, 34), start=0, end=180, fill="white", width=2)
                # Panting, wide-open oval mouth
                draw.ellipse((54, 42, 74, 56), outline="white", width=2)
                # Cute little running sweat droplet on the side of the face
                draw.ellipse((20, 22, 24, 28), fill="white")
                draw.line([(22, 17), (22, 23)], fill="white", width=1)

            case Mood.BORED:
                # Flat, completely unimpressed lines for eyes (-_- style)
                draw.line((32, 24, 48, 24), fill="white", width=3)
                draw.line((80, 24, 96, 24), fill="white", width=3)
                # Small, slightly slanted "meh" mouth
                draw.line((58, 47, 70, 45), fill="white", width=2)

        # Ship the finished face layout to the physical display
        self.device.display(image)

    def display_message(self, message: str) -> None:
        # Kept fallback method just in case you need text elsewhere
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), message, fill="white", font=self.font)
        self.device.display(image)