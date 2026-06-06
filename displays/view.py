from __future__ import annotations

from typing import List, Tuple

from displays.oled import DisplayDevice


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


async def render_menu(
    menu_items: List[str],
    selected_index: int,
    temperature_c: float,
    displays: List[DisplayDevice] | None = None,
) -> None:
    """Render menu to configured display(s).
    
    Args:
        menu_items: List of menu item strings
        selected_index: Index of selected item
        temperature_c: Current temperature in celsius
        displays: List of DisplayDevice instances to render to. If None, prints to stdout.
    """
    if displays is None:
        # Fallback to print if no displays configured
        visible_items, visible_selected = sliding_menu_view(menu_items, selected_index)
        print("\n=== DISPLAY 1: MENU ===")
        for index, item in enumerate(visible_items):
            prefix = "> " if index == visible_selected else "  "
            print(f"{prefix}{item}")
        print("\n=== DISPLAY 2: STATUS ===")
        print(f"Selected: {menu_items[selected_index]}")
        print(f"Temperature: {temperature_c:.1f}°C")
        print("======================\n")
        return

    visible_items, visible_selected = sliding_menu_view(menu_items, selected_index)
    
    # Build display lines
    lines = ["=== MENU ==="]
    for index, item in enumerate(visible_items):
        prefix = "> " if index == visible_selected else "  "
        lines.append(f"{prefix}{item}")
    
    lines.append("")
    lines.append("=== STATUS ===")
    lines.append(f"Selected: {menu_items[selected_index]}")
    lines.append(f"Temp: {temperature_c:.1f}°C")
    
    # Render to all configured displays
    for display in displays:
        await display.display_text(lines)


async def render_screensaver(
    temperature_c: float,
    humidity_percent: float,
    displays: List[DisplayDevice] | None = None,
) -> None:
    """Display screen saver with temperature and humidity.
    
    Args:
        temperature_c: Current temperature in celsius
        humidity_percent: Current humidity percentage
        displays: List of DisplayDevice instances to render to. If None, prints to stdout.
    """
    lines = [
        "=" * 30,
        "|      SCREEN SAVER MODE      |",
        "=" * 30,
        f"|  Temp:  {temperature_c:.1f}°C           |",
        f"|  Humidity: {humidity_percent:.1f}%        |",
        "=" * 30,
    ]
    
    if displays is None:
        # Fallback to print if no displays configured
        print("\n" + "\n".join(lines) + "\n")
        return
    
    # Render to all configured displays
    for display in displays:
        await display.display_text(lines)
