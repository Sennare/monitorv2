"""
Enterprise Web Dashboard API for Remote Monitor.
Designed for 24/7 continuous tablet/mobile kiosk operation.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from typing import Any, AsyncGenerator, Dict, List, Optional

import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# Configuration & Logging
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Ensure repo root is in sys.path regardless of execution working directory
if str(BASE_DIR.parent) not in sys.path:
    sys.path.insert(0, str(BASE_DIR.parent))

load_dotenv(BASE_DIR.parent / ".env")
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("dashboard")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "sensor_data")
DB_USER = os.getenv("DB_USER", "sensor_user")
DB_PASS = os.getenv("DB_PASSWORD", "")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", "1"))
DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", "5"))
DB_TIMEOUT = float(os.getenv("DB_TIMEOUT", "5.0"))

START_TIME = time.time()


# -----------------------------------------------------------------------------
# Database Pool Management
# -----------------------------------------------------------------------------
class DatabaseManager:
    """Manages the asyncpg connection pool with auto-reconnect and health checks."""

    def __init__(self) -> None:
        self.pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        async with self._lock:
            if self.pool is not None and not self.pool._closed:
                return
            try:
                self.pool = await asyncpg.create_pool(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASS,
                    database=DB_NAME,
                    min_size=DB_POOL_MIN,
                    max_size=DB_POOL_MAX,
                    command_timeout=DB_TIMEOUT,
                    timeout=DB_TIMEOUT,
                )
                logger.info(
                    "Connected to PostgreSQL database '%s' at %s:%d (pool size %d-%d)",
                    DB_NAME,
                    DB_HOST,
                    DB_PORT,
                    DB_POOL_MIN,
                    DB_POOL_MAX,
                )
            except Exception as exc:
                logger.warning(
                    "Initial database connection failed (%s). Will retry lazily on request.",
                    exc,
                )
                self.pool = None

    async def close(self) -> None:
        async with self._lock:
            if self.pool is not None:
                await self.pool.close()
                self.pool = None
                logger.info("Database pool closed cleanly.")

    async def get_connection(self) -> asyncpg.pool.PoolAcquireContext:
        """Acquires a connection from pool, attempting auto-reconnect if needed."""
        if self.pool is None or self.pool._closed:
            await self.connect()

        if self.pool is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable. System is attempting to reconnect.",
            )
        return self.pool.acquire()

    async def check_health(self) -> Dict[str, Any]:
        """Checks DB responsiveness and connection pool status."""
        if self.pool is None or self.pool._closed:
            try:
                await self.connect()
            except Exception:
                pass

        if self.pool is None:
            return {
                "connected": False,
                "error": "Database pool is not initialized",
                "pool_size": 0,
                "free_connections": 0,
            }

        try:
            async with self.pool.acquire(timeout=2.0) as conn:
                await conn.fetchval("SELECT 1")
            return {
                "connected": True,
                "error": None,
                "pool_size": self.pool.get_size(),
                "free_connections": self.pool.get_idle_size(),
            }
        except Exception as exc:
            return {
                "connected": False,
                "error": str(exc),
                "pool_size": self.pool.get_size() if self.pool else 0,
                "free_connections": 0,
            }


db_manager = DatabaseManager()


# -----------------------------------------------------------------------------
# Lifespan Management
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application startup and clean teardown."""
    logger.info("Starting Remote Monitor Dashboard API...")
    await db_manager.connect()
    yield
    logger.info("Shutting down Remote Monitor Dashboard API...")
    await db_manager.close()


# -----------------------------------------------------------------------------
# FastAPI App Initialization
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Casa Frizzellato — Remote Monitor Dashboard",
    description="Enterprise environmental telemetry dashboard for 24/7 tablet kiosk display.",
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for local network devices / tablets
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Pydantic Response Models
# -----------------------------------------------------------------------------
class SensorPoint(BaseModel):
    timestamp: datetime
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    temp_min: Optional[float] = None
    temp_max: Optional[float] = None
    hum_min: Optional[float] = None
    hum_max: Optional[float] = None


class LatestReading(BaseModel):
    timestamp: Optional[datetime] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    is_stale: bool = False
    status: str = "ok"


class HistoryResponse(BaseModel):
    timeframe: str
    start_time: datetime
    end_time: datetime
    bucket_seconds: int
    points_count: int
    data: List[SensorPoint]


class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    database: Dict[str, Any]
    server_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# -----------------------------------------------------------------------------
# Downsampling and Query Helpers
# -----------------------------------------------------------------------------
TIMEFRAME_CONFIG: Dict[str, Dict[str, int]] = {
    "6h": {"duration_seconds": 6 * 3600, "bucket_seconds": 120},    # ~180 points
    "12h": {"duration_seconds": 12 * 3600, "bucket_seconds": 180},  # ~240 points
    "24h": {"duration_seconds": 24 * 3600, "bucket_seconds": 300},  # ~288 points
    "3d": {"duration_seconds": 3 * 86400, "bucket_seconds": 900},   # ~288 points
    "7d": {"duration_seconds": 7 * 86400, "bucket_seconds": 1800},  # ~336 points
    "30d": {"duration_seconds": 30 * 86400, "bucket_seconds": 7200},# ~360 points
}


# -----------------------------------------------------------------------------
# Global Exception Handlers
# -----------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled error processing %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Check server logs for details."},
    )


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/health", response_model=HealthResponse, tags=["Monitoring"])
async def get_health() -> HealthResponse:
    """Returns database connection status, pool statistics, and uptime."""
    db_health = await db_manager.check_health()
    overall_status = "healthy" if db_health.get("connected") else "degraded"
    return HealthResponse(
        status=overall_status,
        uptime_seconds=round(time.time() - START_TIME, 1),
        database=db_health,
    )


@app.get("/api/latest", response_model=LatestReading, tags=["Telemetry"])
async def get_latest_reading() -> LatestReading:
    """Returns the most recent single temperature and humidity measurement."""
    try:
        async with await db_manager.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT time, temperature, humidity
                FROM sensor_data
                WHERE temperature IS NOT NULL OR humidity IS NOT NULL
                ORDER BY time DESC
                LIMIT 1
                """
            )

        if not row:
            return LatestReading(
                timestamp=None,
                temperature=None,
                humidity=None,
                is_stale=True,
                status="no_data",
            )

        reading_time = row["time"]
        if reading_time.tzinfo is None:
            reading_time = reading_time.replace(tzinfo=timezone.utc)

        # Flag reading as stale if it hasn't updated in > 30 minutes
        age_seconds = (datetime.now(timezone.utc) - reading_time).total_seconds()
        is_stale = age_seconds > 1800

        temp_val = round(float(row["temperature"]), 2) if row["temperature"] is not None else None
        hum_val = round(float(row["humidity"]), 2) if row["humidity"] is not None else None

        return LatestReading(
            timestamp=reading_time,
            temperature=temp_val,
            humidity=hum_val,
            is_stale=is_stale,
            status="ok",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to query latest reading: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch latest sensor reading: {exc}",
        )


@app.get("/api/history", response_model=HistoryResponse, tags=["Telemetry"])
async def get_history(
    timeframe: str = Query(
        "24h",
        pattern="^(6h|12h|24h|3d|7d|30d)$",
        description="Filter range for telemetry timeseries",
    ),
) -> HistoryResponse:
    """
    Returns time-bucketed historical sensor readings downsampled by PostgreSQL.
    Prevents CPU and RAM saturation on embedded devices while delivering smooth charts.
    """
    config = TIMEFRAME_CONFIG.get(timeframe)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported timeframe '{timeframe}'. Allowed: {list(TIMEFRAME_CONFIG.keys())}",
        )

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(seconds=config["duration_seconds"])
    bucket_sec = config["bucket_seconds"]

    query = """
        SELECT
            to_timestamp(floor(extract(epoch from time) / $3) * $3) AT TIME ZONE 'UTC' AS bucket,
            ROUND(AVG(temperature)::numeric, 2) AS avg_temp,
            ROUND(MIN(temperature)::numeric, 2) AS min_temp,
            ROUND(MAX(temperature)::numeric, 2) AS max_temp,
            ROUND(AVG(humidity)::numeric, 2) AS avg_hum,
            ROUND(MIN(humidity)::numeric, 2) AS min_hum,
            ROUND(MAX(humidity)::numeric, 2) AS max_hum
        FROM sensor_data
        WHERE time >= $1 AND time <= $2
        GROUP BY bucket
        ORDER BY bucket ASC
    """

    try:
        async with await db_manager.get_connection() as conn:
            rows = await conn.fetch(query, start_time, end_time, bucket_sec)

        points: List[SensorPoint] = []
        for r in rows:
            b_time = r["bucket"]
            if b_time.tzinfo is None:
                b_time = b_time.replace(tzinfo=timezone.utc)

            points.append(
                SensorPoint(
                    timestamp=b_time,
                    temperature=float(r["avg_temp"]) if r["avg_temp"] is not None else None,
                    humidity=float(r["avg_hum"]) if r["avg_hum"] is not None else None,
                    temp_min=float(r["min_temp"]) if r["min_temp"] is not None else None,
                    temp_max=float(r["max_temp"]) if r["max_temp"] is not None else None,
                    hum_min=float(r["min_hum"]) if r["min_hum"] is not None else None,
                    hum_max=float(r["max_hum"]) if r["max_hum"] is not None else None,
                )
            )

        return HistoryResponse(
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time,
            bucket_seconds=bucket_sec,
            points_count=len(points),
            data=points,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to query historical data: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database aggregation failed: {exc}",
        )



@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon() -> Response:
    """Handles browser favicon requests silently with 204 No Content."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -----------------------------------------------------------------------------
# Static Files & SPA Serving
# -----------------------------------------------------------------------------
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def serve_index() -> FileResponse:
    """Serves the single-page application index with no-cache headers."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="index.html not found in static folder",
        )
    return FileResponse(
        str(index_file),
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "8000")),
    )
