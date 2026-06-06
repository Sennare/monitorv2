from __future__ import annotations

import asyncio
import random
from typing import AsyncIterator


class HardwareReadError(Exception):
    pass


async def temperature_sensor() -> AsyncIterator[float]:
    while True:
        try:
            await asyncio.sleep(2.0)
            temperature = 22.0 + random.uniform(-2.0, 2.0)
            yield temperature
        except Exception as error:
            print(f"[hal] Temperature sensor error: {error}")
            await asyncio.sleep(1.0)


async def rotary_encoder() -> AsyncIterator[int]:
    step_options = [-1, 0, 1]
    while True:
        try:
            await asyncio.sleep(0.5)
            step = random.choice(step_options)
            yield step
        except Exception as error:
            print(f"[hal] Rotary encoder error: {error}")
            await asyncio.sleep(0.5)
