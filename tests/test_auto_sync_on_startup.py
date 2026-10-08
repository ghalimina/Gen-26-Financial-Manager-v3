#!/usr/bin/env python3
# =============================================================================
# tests/test_auto_sync_on_startup.py — Verification of Auto Cloud-to-Local Git Sync
# =============================================================================

import os
import sys
import time
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from dashboard.app import (
    app,
    auto_sync_from_remote_on_startup,
    is_local_environment,
    _LAST_AUTO_SYNC_STATUS,
    _clear_dashboard_cache,
    _set_dashboard_cached,
    _get_dashboard_cached,
)


class TestAutoSyncOnStartup(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_01_is_local_environment_detection(self):
        """Verifies local workstation detection and cloud container exclusion."""
        # On this workstation with .git present, and no cloud env vars set:
        self.assertTrue(is_local_environment(), "Local developer environment must be detected as True.")

        # In Render container:
        os.environ["RENDER"] = "true"
        try:
            self.assertFalse(is_local_environment(), "Must return False when RENDER is set.")
        finally:
            os.environ.pop("RENDER", None)

        # In GitHub Actions:
        os.environ["GITHUB_ACTIONS"] = "true"
        try:
            self.assertFalse(is_local_environment(), "Must return False when GITHUB_ACTIONS is set.")
        finally:
            os.environ.pop("GITHUB_ACTIONS", None)

    def test_02_auto_sync_non_blocking_background(self):
        """Verifies that calling auto_sync with background=True returns instantly without blocking."""
        t0 = time.time()
        res = auto_sync_from_remote_on_startup(background=True, force=True)
        elapsed = time.time() - t0
        self.assertLess(elapsed, 0.2, "Background call must return in < 200ms.")
        self.assertEqual(res.get("status"), "QUEUED_IN_BACKGROUND")

    def test_03_auto_sync_synchronous_execution(self):
        """Verifies synchronous execution: runs git pull, reloads snapshot, and updates status."""
        res = auto_sync_from_remote_on_startup(background=False, force=True, timeout_sec=15.0)
        self.assertIn(res.get("status"), ["SUCCESS", "WARNING", "TIMEOUT", "SKIPPED"])
        self.assertTrue(res.get("is_local"))
        self.assertTrue(res.get("portfolio_reloaded"))
        self.assertGreaterEqual(res.get("duration_sec"), 0.0)

    def test_04_system_sync_remote_endpoint_get(self):
        """Verifies GET /api/system/sync_remote returns status telemetry."""
        resp = self.client.get("/api/system/sync_remote")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get("status"), "SUCCESS")
        self.assertIn("last_auto_sync", data)
        self.assertIn("is_local_environment", data)

    def test_05_system_sync_remote_endpoint_post(self):
        """Verifies POST /api/system/sync_remote triggers sync and returns HTTP 200."""
        resp = self.client.post("/api/system/sync_remote")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn(data.get("status"), ["SUCCESS", "WARNING", "TIMEOUT", "SKIPPED"])

    def test_06_system_health_includes_auto_sync_status(self):
        """Verifies /api/system/health includes auto_sync_status."""
        resp = self.client.get("/api/system/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("auto_sync_status", data)

    def test_07_thndr_daily_card_reads_disk_snapshot(self):
        """Verifies that /api/thndr_daily_card quickly returns snapshot from disk or generates card."""
        _clear_dashboard_cache()
        t0 = time.time()
        resp = self.client.get("/api/thndr_daily_card")
        elapsed = time.time() - t0
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("thndr_daily_card", data)
        # Verify it loads quickly (sub-1s)
        self.assertLess(elapsed, 1.5)


if __name__ == "__main__":
    unittest.main()
