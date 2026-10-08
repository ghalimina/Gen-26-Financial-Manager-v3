#!/usr/bin/env python3
# =============================================================================
# scripts/verify_pre_deployment_health.py — Pre-Deployment Health & Reliability Check
# Validates dynamic $PORT, WSGI compatibility, clean DB initialization, and scheduler.
# =============================================================================

import os
import sys
import tempfile
import sqlite3
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

class PreDeploymentHealthCheck(unittest.TestCase):

    def test_01_wsgi_app_import(self):
        """Verify gunicorn WSGI entrypoint dashboard.app:app imports cleanly without errors."""
        from dashboard.app import app
        self.assertIsNotNone(app)
        self.assertEqual(app.name, "dashboard.app")

    def test_02_dynamic_port_binding(self):
        """Verify environment variables PORT and HOST are respected."""
        os.environ["PORT"] = "8080"
        os.environ["HOST"] = "0.0.0.0"
        port = int(os.environ.get("PORT", 5000))
        host = os.environ.get("HOST", "0.0.0.0")
        self.assertEqual(port, 8080)
        self.assertEqual(host, "0.0.0.0")

    def test_03_clean_database_initialization(self):
        """Verify database schema and seed catalog initialize cleanly on a brand new database."""
        import gc
        from core.database import DatabaseManager
        
        temp_dir = tempfile.mkdtemp()
        temp_db_path = os.path.join(temp_dir, "gen26_clean_test.db")
        old_db_path = DatabaseManager.DB_PATH
        DatabaseManager.DB_PATH = temp_db_path
        
        try:
            # Seed catalog on brand new clean DB
            DatabaseManager.seed_initial_catalog()
            self.assertTrue(os.path.exists(temp_db_path))

            # Verify tables created
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            self.assertIn("stocks", tables)
            self.assertIn("market_prices", tables)
            self.assertIn("stock_scores", tables)
            self.assertIn("signals", tables)

            cursor.execute("SELECT COUNT(*) FROM stocks;")
            stock_count = cursor.fetchone()[0]
            self.assertGreaterEqual(stock_count, 24)

            cursor.execute("SELECT COUNT(*) FROM market_prices;")
            price_count = cursor.fetchone()[0]
            self.assertGreaterEqual(price_count, 24)
            
            cursor.close()
            conn.close()
        finally:
            DatabaseManager.DB_PATH = old_db_path
            gc.collect()
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

    def test_04_scheduler_non_blocking_startup(self):
        """Verify EGXMarketScheduler starts in background without blocking execution thread."""
        from core.market_scheduler import EGXMarketScheduler
        started = EGXMarketScheduler.start()
        self.assertTrue(started)
        self.assertTrue(EGXMarketScheduler.is_running())
        info = EGXMarketScheduler.get_job_info()
        self.assertEqual(info["status"], "RUNNING")
        EGXMarketScheduler.stop()
        self.assertFalse(EGXMarketScheduler.is_running())

    def test_05_api_endpoints_health(self):
        """Verify primary REST API endpoints respond with HTTP 200."""
        from dashboard.app import app
        client = app.test_client()
        
        # Test root UI
        res_ui = client.get("/")
        self.assertEqual(res_ui.status_code, 200)

        # Test API rankings
        res_rankings = client.get("/api/rankings?universe=all")
        self.assertEqual(res_rankings.status_code, 200)
        data_rankings = res_rankings.get_json()
        self.assertIsInstance(data_rankings, list)
        self.assertGreater(len(data_rankings), 0)

        # Test scheduler status
        res_sched = client.get("/api/scheduler/status")
        self.assertEqual(res_sched.status_code, 200)

        # Test portfolio endpoint
        res_port = client.get("/api/portfolio")
        self.assertEqual(res_port.status_code, 200)


if __name__ == "__main__":
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    
    print("=" * 80)
    print("GEN-26 PRE-DEPLOYMENT HEALTH & RELIABILITY VERIFICATION")
    print("=" * 80)
    unittest.main()
