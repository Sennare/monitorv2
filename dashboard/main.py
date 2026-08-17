import os
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

import asyncpg
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "sensor_data")
DB_USER = os.getenv("DB_USER", "sensor_user")
DB_PASS = os.getenv("DB_PASSWORD", "")
DB_PORT = int(os.getenv("DB_PORT", 5432))

app = FastAPI(title="Temperature & Humidity Dashboard API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# serve the dashboard files (index.html, app.js) under /static
app.mount("/static", StaticFiles(directory=os.path.dirname(__file__), html=True), name="static")

# root endpoint serves index.html for single-page experience
@app.get("/", include_in_schema=False)
def root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))

pool: asyncpg.Pool | None = None


class DataPoint(BaseModel):
    timestamp: datetime
    temperature: float | None
    humidity: float | None


@app.on_event("startup")
async def startup():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            min_size=1,
            max_size=5,
        )


@app.on_event("shutdown")
async def shutdown():
    global pool
    if pool:
        await pool.close()


def _interpret_timeframe(timeframe: str) -> Tuple[datetime, int, int]:
    now = datetime.now(timezone.utc)
    if timeframe == "24h":
        total_seconds = 24 * 3600
        slot_seconds = 5 * 60
    elif timeframe == "7d":
        total_seconds = 7 * 24 * 3600
        slot_seconds = 3600
    elif timeframe == "1m":
        total_seconds = 30 * 24 * 3600
        slot_seconds = 24 * 3600
    else:
        raise ValueError("Unsupported timeframe")

    slots = int(total_seconds // slot_seconds)
    start_time = now - timedelta(seconds=total_seconds)
    return start_time, slot_seconds, slots


@app.get("/api/data", response_model=List[DataPoint])
async def get_data(timeframe: str = Query("24h", pattern="^(24h|7d|1m)$")):
    global pool
    if pool is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    try:
        start_time, slot_seconds, slots = _interpret_timeframe(timeframe)
        end_time = datetime.now(timezone.utc)

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT time, temperature, humidity FROM sensor_data WHERE time BETWEEN $1 AND $2 ORDER BY time",
                start_time,
                end_time,
            )

        temps: List[List[float]] = [[] for _ in range(slots)]
        hums: List[List[float]] = [[] for _ in range(slots)]

        for r in rows:
            t = r["time"]
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            delta = t - start_time
            slot = int(delta.total_seconds() // slot_seconds)
            if slot < 0:
                continue
            if slot >= slots:
                slot = slots - 1
            temp = r["temperature"]
            hum = r["humidity"]
            if temp is not None:
                try:
                    temps[slot].append(float(temp))
                except Exception:
                    pass
            if hum is not None:
                try:
                    hums[slot].append(float(hum))
                except Exception:
                    pass

        result: List[DataPoint] = []
        for i in range(slots):
            ts = start_time + timedelta(seconds=i * slot_seconds)
            temp_avg = None
            hum_avg = None
            if temps[i]:
                temp_avg = sum(temps[i]) / len(temps[i])
            if hums[i]:
                hum_avg = sum(hums[i]) / len(hums[i])
            result.append(DataPoint(timestamp=ts, temperature=temp_avg, humidity=hum_avg))

        return result
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timeframe")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
