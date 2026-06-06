from __future__ import annotations

from typing import Sequence

from core.state import AppState


def clamp_index(index: int, count: int) -> int:
    if count <= 0:
        return 0
    return max(0, min(index, count - 1))


def scroll_menu(state: AppState, steps: int) -> None:
    new_index = clamp_index(state.selected_index + steps, len(state.menu_items))
    if new_index != state.selected_index:
        state.selected_index = new_index


def update_temperature(state: AppState, temperature_c: float) -> None:
    state.temperature_c = temperature_c


def reset_menu(state: AppState) -> None:
    state.selected_index = 0
