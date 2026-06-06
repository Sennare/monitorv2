from __future__ import annotations

from typing import List, Tuple


def sliding_menu_view(menu_items: List[str], selected_index: int, window_size: int = 4) -> Tuple[List[str], int]:
    count = len(menu_items)
    if count <= window_size:
        return menu_items, selected_index

    half_window = window_size // 2
    start = selected_index - half_window
    if start < 0:
        start = 0
    if start + window_size > count:
        start = count - window_size

    visible_items = menu_items[start : start + window_size]
    visible_selected = selected_index - start
    return visible_items, visible_selected


def render_menu(menu_items: List[str], selected_index: int, temperature_c: float) -> None:
    visible_items, visible_selected = sliding_menu_view(menu_items, selected_index)

    print("\n=== DISPLAY 1: MENU ===")
    for index, item in enumerate(visible_items):
        prefix = "> " if index == visible_selected else "  "
        print(f"{prefix}{item}")

    print("\n=== DISPLAY 2: STATUS ===")
    print(f"Selected: {menu_items[selected_index]}")
    print(f"Temperature: {temperature_c:.1f}°C")
    print("======================\n")
