from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class AppState:
    menu_items: List[str] = field(default_factory=lambda: [
        "Home",
        "Status",
        "Sensors",
        "Settings",
        "About",
        "Shutdown",
    ])
    selected_index: int = 0
    temperature_c: float = 22.0
    humidity_percent: float = 50.0
    is_idle: bool = True

    def selected_item(self) -> str:
        return self.menu_items[self.selected_index]
