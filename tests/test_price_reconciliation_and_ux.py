#!/usr/bin/env python3
# =============================================================================
# tests/test_price_reconciliation_and_ux.py — Market Data Reconciliation & Beginner UX Tests
# Validates price reconciliation against raw feeds, EOD classification,
# company dropdown selectors, and beginner-friendly explanatory tooltips.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.price_reconciliation import PriceReconciliationEngine
from dashboard.app import app


class TestPriceReconciliationAndUX(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        res = self.client.get("/")
        self.html = res.get_data(as_text=True)

    def test_01_price_reconciliation_engine_runs_cleanly(self):
        """Verify that price reconciliation analyzes key liquid assets without errors."""
        report = PriceReconciliationEngine.perform_reconciliation()
        self.assertGreaterEqual(report["sample_stocks_audited"], 5)
        self.assertEqual(report["data_source_labeling"], "OFFICIAL_EGX_LAST_CLOSE")

        comi_rec = next(r for r in report["results"] if r["ticker"] == "COMI.CA")
        self.assertEqual(comi_rec["displayed_price"], 137.00)
        self.assertEqual(comi_rec["price_classification"], "OFFICIAL_LAST_CLOSE")

    def test_02_company_selector_dropdown_exists_in_dom(self):
        """Verify that Real Portfolio and Watchlist have company selector dropdowns."""
        self.assertIn('id="modal-company-select"', self.html)
        self.assertIn('id="watchlist-select"', self.html)
        self.assertIn('value="COMI.CA|137.00"', self.html)
        self.assertIn('value="SWDY.CA|116.00"', self.html)

    def test_03_beginner_guidance_boxes_rendered(self):
        """Verify that beginner guidance boxes and plain language rationale are present."""
        self.assertIn("دليل المبتدئين السريع", self.html)
        self.assertIn("كيف تقرأ هذا الجدول؟", self.html)
        self.assertIn("لماذا تم اختياره؟", self.html)

    def test_04_official_eod_data_labeling_present(self):
        """Verify prices are clearly identified as official closing prices with timestamp."""
        self.assertIn("إغلاق رسمي", self.html)


if __name__ == "__main__":
    unittest.main()
