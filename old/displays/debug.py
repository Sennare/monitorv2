from __future__ import annotations

from displays.oled import DisplayDevice


class DebugDisplay(DisplayDevice):
    """Debug display that prints output using print() statements."""

    def __init__(self) -> None:
        self._initialized = False
        self._current_content: list[str] = []

    async def initialize(self) -> None:
        self._initialized = True
        print("[debug] Debug display initialized")

    async def close(self) -> None:
        self._initialized = False
        print("[debug] Debug display closed")

    async def display_text(self, lines: list[str]) -> None:
        if not self._initialized:
            raise RuntimeError("DebugDisplay is not initialized")
        self._current_content = lines
        print("[debug] Output:")
        for line in lines:
            print(f"  {line}")

    async def clear(self) -> None:
        if not self._initialized:
            raise RuntimeError("DebugDisplay is not initialized")
        self._current_content = []
        print("[debug] Screen cleared")
