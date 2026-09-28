"""
Automated unit tests for the Enterprise Dashboard.
Validates backend configurations, endpoints, static assets, and client engine files.
"""

import os
import py_compile
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = BASE_DIR / "dashboard"
STATIC_DIR = DASHBOARD_DIR / "static"


class TestDashboardStaticFiles(unittest.TestCase):
    """Verifies all static assets exist, are non-empty, and contain required kiosk features."""

    def test_index_html_structure(self):
        index_file = STATIC_DIR / "index.html"
        self.assertTrue(index_file.is_file(), "index.html must exist in static/")
        content = index_file.read_text(encoding="utf-8")

        # Verify Title
        self.assertIn("Casa Frizzellato", content)

        # Verify Canvas and Tooltip
        self.assertIn('id="mainChart"', content)
        self.assertIn('id="chartTooltip"', content)

        # Verify Kiosk controls
        self.assertIn('id="btnWakeLock"', content)
        self.assertIn('id="btnFullscreen"', content)

        # Verify Telemetry Cards
        self.assertIn('id="valTemp"', content)
        self.assertIn('id="valHum"', content)
        self.assertIn('id="statusPill"', content)

        # Verify Timeframe Buttons (6h, 12h, 24h, 3d, 7d, 30d)
        for tf in ["6h", "12h", "24h", "3d", "7d", "30d"]:
            self.assertIn(f'data-timeframe="{tf}"', content)

    def test_css_rules(self):
        css_file = STATIC_DIR / "css" / "style.css"
        self.assertTrue(css_file.is_file(), "style.css must exist in static/css/")
        content = css_file.read_text(encoding="utf-8")

        # Verify Dark mode palette and variables
        self.assertIn("--bg-primary", content)
        self.assertIn("--color-temp", content)
        self.assertIn("--color-hum", content)
        self.assertIn("100dvh", content)

        # Verify Responsive rules
        self.assertIn("@media (max-width: 768px)", content)

    def test_chart_engine_js(self):
        chart_js = STATIC_DIR / "js" / "chart_engine.js"
        self.assertTrue(chart_js.is_file(), "chart_engine.js must exist in static/js/")
        content = chart_js.read_text(encoding="utf-8")

        # Verify TelemetryChart class and methods
        self.assertIn("class TelemetryChart", content)
        self.assertIn("setData(", content)
        self.assertIn("resize(", content)
        self.assertIn("render(", content)
        self.assertIn("destroy(", content)
        self.assertIn("devicePixelRatio", content)

    def test_app_js(self):
        app_js = STATIC_DIR / "js" / "app.js"
        self.assertTrue(app_js.is_file(), "app.js must exist in static/js/")
        content = app_js.read_text(encoding="utf-8")

        # Verify auto-refresh, backoff, and wake lock
        self.assertIn("REFRESH_INTERVAL_MS", content)
        self.assertIn("BASE_RETRY_DELAY_MS", content)
        self.assertIn("wakeLock", content)
        self.assertIn("visibilitychange", content)
        self.assertIn("/api/history", content)
        self.assertIn("/api/latest", content)


class TestDashboardBackend(unittest.TestCase):
    """Verifies backend syntax, requirements, and database schema."""

    def test_main_py_compilation(self):
        main_file = DASHBOARD_DIR / "main.py"
        self.assertTrue(main_file.is_file(), "main.py must exist in dashboard/")
        # py_compile checks syntax without executing
        compiled = py_compile.compile(str(main_file), doraise=True)
        self.assertIsNotNone(compiled)

    def test_requirements_file(self):
        req_file = DASHBOARD_DIR / "requirements.txt"
        self.assertTrue(req_file.is_file(), "requirements.txt must exist")
        content = req_file.read_text(encoding="utf-8")
        self.assertIn("fastapi", content)
        self.assertIn("uvicorn", content)
        self.assertIn("asyncpg", content)
        self.assertIn("pydantic", content)

    def test_schema_sql(self):
        schema_file = DASHBOARD_DIR / "schema.sql"
        self.assertTrue(schema_file.is_file(), "schema.sql must exist")
        content = schema_file.read_text(encoding="utf-8")
        self.assertIn("CREATE TABLE IF NOT EXISTS sensor_data", content)
        self.assertIn("CREATE INDEX IF NOT EXISTS idx_sensor_data_time", content)

    def test_timeframe_durations(self):
        # Verify logical ratios of timeframe intervals
        timeframes = {
            "6h": {"duration": 6 * 3600, "bucket": 120},
            "12h": {"duration": 12 * 3600, "bucket": 180},
            "24h": {"duration": 24 * 3600, "bucket": 300},
            "3d": {"duration": 3 * 86400, "bucket": 900},
            "7d": {"duration": 7 * 86400, "bucket": 1800},
            "30d": {"duration": 30 * 86400, "bucket": 7200},
        }

        for tf, conf in timeframes.items():
            num_points = conf["duration"] // conf["bucket"]
            # Points count should be manageable for embedded/tablet rendering (between 100 and 400)
            self.assertGreaterEqual(num_points, 100, f"Too few points for {tf}: {num_points}")
            self.assertLessEqual(num_points, 400, f"Too many points for {tf}: {num_points}")

    def test_standard_endpoints_present(self):
        main_content = (DASHBOARD_DIR / "main.py").read_text(encoding="utf-8")
        self.assertIn('"/api/history"', main_content)
        self.assertIn('"/api/latest"', main_content)
        self.assertIn('"/api/health"', main_content)
        self.assertIn('"/favicon.ico"', main_content)


if __name__ == "__main__":
    unittest.main()
