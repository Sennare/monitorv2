from luma.core.interface.serial import i2c
from luma.core.interface.parallel import bitbang_6800
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

class OledDisplay:
    def __init__(self):
        serial = i2c(port=1, address=0x3C)
        self.device = ssd1306(serial, width=128, height=64, rotate=0)
        self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)

    def display_message(self, message: str) -> None:
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), message, fill="white", font=self.font)
        self.device.display(image)