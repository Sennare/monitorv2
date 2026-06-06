from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class DisplayDevice(ABC):
    @abstractmethod
    async def initialize(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def display_text(self, lines: list[str]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        raise NotImplementedError


class MockOLEDDisplay(DisplayDevice):
    def __init__(self, width: int = 128, height: int = 64) -> None:
        self._width = width
        self._height = height
        self._initialized = False
        self._current_content: list[str] = []

    async def initialize(self) -> None:
        self._initialized = True
        print(f"[display] Mock OLED initialized: {self._width}x{self._height}")

    async def close(self) -> None:
        self._initialized = False
        print("[display] Mock OLED closed")

    async def display_text(self, lines: list[str]) -> None:
        if not self._initialized:
            raise RuntimeError("MockOLEDDisplay is not initialized")
        self._current_content = lines
        print("[display] Rendering to OLED:")
        for line in lines:
            print(f"  {line}")

    async def clear(self) -> None:
        if not self._initialized:
            raise RuntimeError("MockOLEDDisplay is not initialized")
        self._current_content = []
        print("[display] Screen cleared")


class RealOLEDDisplay(DisplayDevice):
    def __init__(
        self,
        port: int = 1,
        address: int = 0x3C,
        width: int = 128,
        height: int = 64,
        font_path: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        font_size: int = 12,
    ) -> None:
        self._port = port
        self._address = address
        self._width = width
        self._height = height
        self._font_path = font_path
        self._font_size = font_size

        self._device: Optional[object] = None
        self._font: Optional[object] = None
        self._image: Optional[object] = None
        self._draw: Optional[object] = None

    async def initialize(self) -> None:
        try:
            from luma.oled.device import ssd1306
            from luma.core.interface.serial import i2c
            from PIL import Image, ImageDraw, ImageFont

            serial = i2c(port=self._port, address=self._address)
            self._device = ssd1306(serial, width=self._width, height=self._height, rotate=0)
            self._font = ImageFont.truetype(self._font_path, self._font_size)
            self._image = Image.new("1", (self._width, self._height))
            self._draw = ImageDraw.Draw(self._image)

            print(
                f"[display] Real OLED initialized at 0x{self._address:02X} on port {self._port}"
            )
        except ImportError as e:
            print(f"[display] Required libraries not installed: {e}")
            raise
        except Exception as e:
            print(f"[display] Error initializing OLED: {e}")
            raise

    async def close(self) -> None:
        if self._device:
            try:
                self._device.display(Image.new("1", (self._width, self._height)))
                print("[display] Real OLED closed")
            except Exception as e:
                print(f"[display] Error closing OLED: {e}")

    async def display_text(self, lines: list[str]) -> None:
        if not self._device or not self._draw or not self._image or not self._font:
            raise RuntimeError("RealOLEDDisplay is not initialized")

        try:
            self._draw.rectangle((0, 0, self._width, self._height), fill=0)
            y_offset = 0
            for line in lines:
                self._draw.text((0, y_offset), line, font=self._font, fill=1)
                y_offset += 12

            self._device.display(self._image)
        except Exception as e:
            print(f"[display] Error displaying text on OLED: {e}")
            raise

    async def clear(self) -> None:
        if not self._device or not self._image:
            raise RuntimeError("RealOLEDDisplay is not initialized")

        try:
            from PIL import Image

            self._image = Image.new("1", (self._width, self._height))
            self._device.display(self._image)
        except Exception as e:
            print(f"[display] Error clearing OLED: {e}")
            raise
