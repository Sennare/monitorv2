# Monitor v2 - Multi-Task Idle State Application

## Overview
A fully integrated Python application that runs in idle state with a screen saver, background sensor monitoring, and periodic database storage.

## Features

### 1. **Idle State Screen Saver** 
- Displays current temperature and humidity
- Cycle: 10 seconds ON → 30 seconds OFF (repeating)
- Continuously loops while application is running

### 2. **Background Sensor Reading**
- Reads temperature from hardware every 30 seconds
- Reads humidity from hardware every 30 seconds
- Updates application state with latest readings
- Handles sensor errors gracefully

### 3. **Database Storage**
- Stores temperature and humidity measurements every 5 minutes
- Uses `WeatherMeasurement` dataclass
- Persists through `MockWeatherRepository` (or real PostgreSQL when configured)
- Maintains measurement history with timestamps

### 4. **User Input Monitoring**
- Continuously monitors rotary encoder
- Ready for user interaction (can exit idle state or navigate menus)
- Runs in background without blocking other tasks

## Architecture

### Task Structure
All tasks run concurrently using Python's `asyncio`:

```
Application
├── sensor_reader()           [Runs every 30s]
├── database_writer()         [Runs every 5 min]
├── screensaver_loop()        [10s ON / 30s OFF cycle]
└── monitor_encoder()         [Continuous monitoring]
```

### Module Organization
```
monitorv2/
├── main.py                   # Entry point & Application class
├── core/
│   ├── state.py             # AppState dataclass (temp, humidity, idle flag)
│   └── logic.py             # State update functions
├── displays/
│   ├── view.py              # Screen saver rendering
│   └── oled.py              # Display device abstraction
├── hardware/
│   └── hal.py               # Temperature & humidity sensors, encoder
├── storage/
│   ├── db.py                # Database client abstraction
│   └── weather.py           # Weather measurement model & repository
```

## Running the Application

### Prerequisites
```bash
cd /home/elia/workspace/monitorv2
```

### Start Application
```bash
python3 main.py
```

### Expected Output
```
[app] Starting monitor application...
[app] Sensor reader started
[app] Database writer started
[app] Screen saver started

==============================
|      SCREEN SAVER MODE      |
==============================
|  Temp:  22.0°C           |
|  Humidity: 50.0%        |
==============================

[app] Encoder monitor started
[db] Mock database connected
```

### Stop Application
- Press `Ctrl+C` to gracefully shutdown
- Application will:
  - Stop all background tasks
  - Close database connection
  - Exit cleanly

## Timing Overview

| Task | Interval |
|------|----------|
| Sensor Read | Every 30 seconds |
| Database Store | Every 5 minutes (300 seconds) |
| Display ON | 10 seconds |
| Display OFF | 30 seconds |

## Current Implementation Details

### State Management
- **AppState** tracks: menu items, selected index, temperature, humidity, idle flag
- Single source of truth for application state
- Thread-safe for concurrent access (asyncio single thread)

### Sensor Integration
- Mock sensors generate random values for testing
- Temperature: ~22°C ± 2°C
- Humidity: ~50% ± 10%
- Easy to replace with real hardware implementations

### Database Integration
- Uses `MockWeatherRepository` for development
- Stores `WeatherMeasurement` objects (temp, humidity, timestamp)
- Ready for PostgreSQL integration via `PostgresWeatherRepository`

### Display System
- Simple text-based console output for testing
- `render_screensaver()` shows idle state display
- Ready to integrate with actual OLED hardware via `DisplayDevice` abstraction

## Future Enhancements

1. **Menu Navigation**: Extend with user interaction to exit idle state
2. **Real Hardware**: 
   - Connect actual temperature/humidity sensors (DHT22, BME680, etc.)
   - Implement real OLED display rendering
   - Wire rotary encoder input
3. **Database**: Switch from mock to real PostgreSQL backend
4. **Logging**: Add structured logging system
5. **Configuration**: Load settings from config files
6. **Error Recovery**: Implement retry logic and failover strategies

## Development Notes

- All components use async/await for non-blocking operation
- Clean separation of concerns (hardware, display, state, storage)
- Mock implementations allow testing without hardware
- Application gracefully handles interrupts and timeouts
- Extensible architecture for adding new features
