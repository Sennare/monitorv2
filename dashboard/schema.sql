-- Schema definition for remote-monitor sensor telemetry
-- PostgreSQL table: sensor_data

CREATE TABLE IF NOT EXISTS sensor_data (
    id SERIAL PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION
);

-- Essential index for time-range filtering and downsampled aggregations
CREATE INDEX IF NOT EXISTS idx_sensor_data_time ON sensor_data (time DESC);
