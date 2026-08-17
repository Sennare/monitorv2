-- SQL script to create the sensor_data table
-- Run in your Postgres database (psql -f create_table.sql)

CREATE TABLE IF NOT EXISTS sensor_data (
    id SERIAL PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION
);

-- Optional index to speed up timeframe queries
CREATE INDEX IF NOT EXISTS idx_sensor_data_time ON sensor_data (time);
