from __future__ import annotations

import asyncio
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class DatabaseConfig:
    host: str
    database: str
    user: str
    password: Optional[str] = None
    port: int = 5432
    connect_timeout: int = 5


class DatabaseClient(ABC):
    async def connect(self) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def persist_sensor_reading(
        self, sensor_name: str, value: float, timestamp: datetime
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def fetch_sensor_readings(
        self, sensor_name: str, since: datetime
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError


class MockDatabaseClient(DatabaseClient):
    def __init__(self) -> None:
        self._connected = False
        self._rows: List[Dict[str, Any]] = []

    async def connect(self) -> None:
        await asyncio.sleep(0.05)
        self._connected = True
        print("[db] Mock database connected")

    async def close(self) -> None:
        if self._connected:
            await asyncio.sleep(0.01)
            self._connected = False
            print("[db] Mock database closed")

    def _ensure_connected(self) -> None:
        if not self._connected:
            raise RuntimeError("MockDatabaseClient is not connected")

    async def persist_sensor_reading(
        self, sensor_name: str, value: float, timestamp: datetime
    ) -> None:
        self._ensure_connected()
        record = {
            "sensor_name": sensor_name,
            "value": value,
            "timestamp": timestamp,
        }
        self._rows.append(record)
        print(f"[db] Persisted reading: {record}")

    async def fetch_sensor_readings(
        self, sensor_name: str, since: datetime
    ) -> List[Dict[str, Any]]:
        self._ensure_connected()
        return [
            row
            for row in self._rows
            if row["sensor_name"] == sensor_name and row["timestamp"] >= since
        ]


class PostgresDatabaseClient(DatabaseClient):
    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config
        self._connection: Optional[Any] = None
        self._connected = False

    async def connect(self) -> None:
        def sync_connect() -> Any:
            import psycopg2

            return psycopg2.connect(
                host=self._config.host,
                database=self._config.database,
                user=self._config.user,
                password=self._config.password,
                port=self._config.port,
                connect_timeout=self._config.connect_timeout,
            )

        try:
            self._connection = await asyncio.to_thread(sync_connect)
            self._connected = True
            print("[db] Postgres database connected")
        except ImportError:
            print("[db] psycopg2 is not installed. Use MockDatabaseClient for local testing.")
            raise
        except Exception as error:
            print(f"[db] Error connecting to Postgres: {error}")
            raise

    async def close(self) -> None:
        if self._connection:
            await asyncio.to_thread(self._connection.close)
            self._connected = False
            print("[db] Postgres database closed")

    async def persist_sensor_reading(
        self, sensor_name: str, value: float, timestamp: datetime
    ) -> None:
        if not self._connection:
            raise RuntimeError("PostgresDatabaseClient is not connected")

        def execute() -> None:
            with self._connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO sensor_readings (sensor_name, value, timestamp) VALUES (%s, %s, %s)",
                    (sensor_name, value, timestamp),
                )
                self._connection.commit()

        await asyncio.to_thread(execute)

    async def fetch_sensor_readings(
        self, sensor_name: str, since: datetime
    ) -> List[Dict[str, Any]]:
        if not self._connection:
            raise RuntimeError("PostgresDatabaseClient is not connected")

        def execute() -> List[Dict[str, Any]]:
            with self._connection.cursor() as cursor:
                cursor.execute(
                    "SELECT sensor_name, value, timestamp FROM sensor_readings WHERE sensor_name = %s AND timestamp >= %s ORDER BY timestamp DESC",
                    (sensor_name, since),
                )
                rows = cursor.fetchall()
                return [
                    {"sensor_name": row[0], "value": row[1], "timestamp": row[2]}
                    for row in rows
                ]

        return await asyncio.to_thread(execute)


def build_postgres_config() -> DatabaseConfig:
    return DatabaseConfig(
        host="localhost",
        database="sensor_data",
        user="sensor_user",
        password=os.environ.get("SENSOR_DB_PASSWORD"),
    )
