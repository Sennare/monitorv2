from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

from core.logic import scroll_menu, update_temperature
from core.state import AppState
from displays.view import render_menu
from hardware.hal import rotary_encoder, temperature_sensor
from storage.db import DatabaseClient, MockDatabaseClient


async def monitor_temperature(
    state: AppState,
    display_event: asyncio.Event,
    db_client: DatabaseClient,
) -> None:
    async for temperature_c in temperature_sensor():
        update_temperature(state, temperature_c)
        await db_client.persist_sensor_reading(
            "temperature", temperature_c, datetime.utcnow()
        )
        display_event.set()


async def monitor_encoder(state: AppState, display_event: asyncio.Event) -> None:
    async for step in rotary_encoder():
        if step == 0:
            continue
        scroll_menu(state, step)
        display_event.set()


async def display_loop(state: AppState, display_event: asyncio.Event) -> None:
    last_rendered_index: Optional[int] = None
    last_temperature: Optional[float] = None

    while True:
        await display_event.wait()
        display_event.clear()

        if (
            last_rendered_index != state.selected_index
            or last_temperature != state.temperature_c
        ):
            render_menu(state.menu_items, state.selected_index, state.temperature_c)
            last_rendered_index = state.selected_index
            last_temperature = state.temperature_c


async def main() -> None:
    state = AppState()
    display_event = asyncio.Event()
    display_event.set()

    db_client: DatabaseClient = MockDatabaseClient()
    await db_client.connect()

    tasks = [
        asyncio.create_task(monitor_temperature(state, display_event, db_client)),
        asyncio.create_task(monitor_encoder(state, display_event)),
        asyncio.create_task(display_loop(state, display_event)),
    ]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for task in tasks:
            task.cancel()
    finally:
        await db_client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
