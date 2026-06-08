from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class WeatherMeasurement:
    temperature_c: float
    humidity_percent: float
    timestamp: datetime


class WeatherRepository(ABC):
    @abstractmethod
    async def persist_measurement(self, measurement: WeatherMeasurement) -> None:
        raise NotImplementedError

    @abstractmethod
    async def fetch_measurements_in_range(
        self, start: datetime, end: datetime
    ) -> List[WeatherMeasurement]:
        raise NotImplementedError


class MockWeatherRepository(WeatherRepository):
    def __init__(self) -> None:
        self._measurements: List[WeatherMeasurement] = []

    async def persist_measurement(self, measurement: WeatherMeasurement) -> None:
        self._measurements.append(measurement)
        print(
            f"[weather] Persisted: temp={measurement.temperature_c}°C, "
            f"humidity={measurement.humidity_percent}% at {measurement.timestamp}"
        )

    async def fetch_measurements_in_range(
        self, start: datetime, end: datetime
    ) -> List[WeatherMeasurement]:
        return [
            m
            for m in self._measurements
            if start <= m.timestamp <= end
        ]


class PostgresWeatherRepository(WeatherRepository):
    def __init__(self, connection: Any) -> None:
        self._connection = connection

    async def persist_measurement(self, measurement: WeatherMeasurement) -> None:
        if not self._connection:
            raise RuntimeError("PostgresWeatherRepository is not connected")

        def execute() -> None:
            with self._connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO weather_measurements (temperature_c, humidity_percent, timestamp) VALUES (%s, %s, %s)",
                    (
                        measurement.temperature_c,
                        measurement.humidity_percent,
                        measurement.timestamp,
                    ),
                )
                self._connection.commit()

        await asyncio.to_thread(execute)

    async def fetch_measurements_in_range(
        self, start: datetime, end: datetime
    ) -> List[WeatherMeasurement]:
        if not self._connection:
            raise RuntimeError("PostgresWeatherRepository is not connected")

        def execute() -> List[WeatherMeasurement]:
            with self._connection.cursor() as cursor:
                cursor.execute(
                    "SELECT temperature_c, humidity_percent, timestamp FROM weather_measurements WHERE timestamp BETWEEN %s AND %s ORDER BY timestamp ASC",
                    (start, end),
                )
                rows = cursor.fetchall()
                return [
                    WeatherMeasurement(
                        temperature_c=row[0],
                        humidity_percent=row[1],
                        timestamp=row[2],
                    )
                    for row in rows
                ]

        return await asyncio.to_thread(execute)
