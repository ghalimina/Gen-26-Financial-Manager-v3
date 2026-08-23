#!/usr/bin/env python3
# =============================================================================
# tests/ui/test_arabic_dictionary.py — GEN-26 Arabic Terminology Unit Tests
# Validates single source of truth for Arabic financial labels and translations.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.arabic_dictionary import ArabicFinancialDictionary


class TestArabicDictionary(unittest.TestCase):

    def test_01_core_navigation_terms_present(self):
        """Verify that all main dashboard navigation sections have Arabic translations."""
        for key in ["dashboard", "market_overview", "stock_ranking", "stock_details", "my_real_portfolio", "paper_portfolio", "risk_center"]:
            val = ArabicFinancialDictionary.get(key)
            self.assertTrue(len(val) > 0)
            self.assertNotEqual(val, key)

    def test_02_financial_actions_present(self):
        """Verify BUY, WATCH, HOLD, REDUCE, EXIT translations."""
        self.assertIn("شراء", ArabicFinancialDictionary.get("BUY"))
        self.assertIn("مراقبة", ArabicFinancialDictionary.get("WATCH"))
        self.assertIn("احتفاظ", ArabicFinancialDictionary.get("HOLD"))
        self.assertIn("تخفيض", ArabicFinancialDictionary.get("REDUCE"))
        self.assertIn("خروج", ArabicFinancialDictionary.get("EXIT"))


if __name__ == "__main__":
    unittest.main()
