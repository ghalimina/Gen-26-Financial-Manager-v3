#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_egx_universe.py — GEN-26 EGX Universe Discovery & Audit Unit Tests
# Validates 100% real EGX equities auditing and isolated mock partitioning for edge cases.
# =============================================================================

import unittest
from unittest.mock import patch
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.egx_universe import EGXUniverseAuditor, SecurityStatus


class TestEGXUniverse(unittest.TestCase):

    def test_01_universe_audit_real_universe(self):
        """
        Verify that audit_universe audits the real 200+ active EGX equities catalog.
        """
        report = EGXUniverseAuditor.audit_universe("2026-08-20")

        self.assertGreaterEqual(report["total_discovered"], 200)
        self.assertGreaterEqual(report["tradable_count"], 200)
        self.assertIn("FULL_UNIVERSE", report["coverage_status"])

        # Check JSON output file exists
        json_path = os.path.join(WORKSPACE, "reports", "egx_universe.json")
        self.assertTrue(os.path.exists(json_path))

    def test_02_isolated_mock_partitioning_for_edge_cases(self):
        """
        Verify status partitioning using isolated test mock fixtures without polluting production catalogs.
        """
        mock_catalog = [
            {"ticker": "COMI.CA", "name": "Commercial International Bank", "sector": "Banking", "isin": "EGS60121C018", "is_core": True},
            {"ticker": "MOCK_SUSP.CA", "name": "Test Suspended Stock", "sector": "Industrial", "isin": "EGS000000001", "is_core": False, "force_status": SecurityStatus.SUSPENDED, "exclusion_reason": "DISCLOSURE_HALT"},
            {"ticker": "MOCK_ILLIQ.CA", "name": "Test Illiquid Stock", "sector": "Consumer", "isin": "EGS000000002", "is_core": False, "force_status": SecurityStatus.ILLIQUID, "exclusion_reason": "LOW_ADV"},
            {"ticker": "MOCK_MISS.CA", "name": "Test Missing Stock", "sector": "General", "isin": "EGS000000003", "is_core": False, "force_status": SecurityStatus.MISSING_DATA, "exclusion_reason": "NO_BARS"},
            {"ticker": "MOCK_DELIST.CA", "name": "Test Delisted Stock", "sector": "Real Estate", "isin": "EGS000000004", "is_core": False, "force_status": SecurityStatus.DELISTED, "exclusion_reason": "DELISTED_EGX"}
        ]

        with patch.object(EGXUniverseAuditor, "EGX_CATALOG", mock_catalog):
            report = EGXUniverseAuditor.audit_universe("2026-08-20")
            self.assertEqual(report["total_discovered"], 5)
            self.assertEqual(report["tradable_count"], 1)
            self.assertEqual(report["suspended_count"], 1)
            self.assertEqual(report["illiquid_count"], 1)
            self.assertEqual(report["missing_data_count"], 1)
            self.assertEqual(report["delisted_count"], 1)

    def test_03_every_excluded_security_has_reason(self):
        """
        Verify that no security is categorized as non-tradable without an explicit reason code.
        """
        report = EGXUniverseAuditor.audit_universe("2026-08-20")
        for sec in report["securities"]:
            self.assertIn("status", sec)
            self.assertIn("status_reason", sec)
            if sec["status"] != SecurityStatus.TRADABLE:
                self.assertNotEqual(sec["status_reason"], "")


if __name__ == "__main__":
    unittest.main()
