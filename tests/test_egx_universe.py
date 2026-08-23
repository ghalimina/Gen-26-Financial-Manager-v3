#!/usr/bin/env python3
# =============================================================================
# tests/test_egx_universe.py — GEN-26 EGX Universe Discovery & Audit Unit Tests
# Validates security partitioning, tradability status, and exclusion reasons.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.egx_universe import EGXUniverseAuditor, SecurityStatus


class TestEGXUniverse(unittest.TestCase):

    def test_01_universe_audit_structure_and_coverage(self):
        """
        Verify that audit_universe generates properly categorized report
        and explicitly tags partial universe status.
        """
        report = EGXUniverseAuditor.audit_universe("2026-08-20")

        self.assertGreaterEqual(report["total_discovered"], 30)
        self.assertEqual(report["tradable_count"], 27) # Core 27
        self.assertGreaterEqual(report["suspended_count"], 1)
        self.assertGreaterEqual(report["illiquid_count"], 1)
        self.assertGreaterEqual(report["missing_data_count"], 1)
        self.assertGreaterEqual(report["delisted_count"], 1)

        # Must be explicitly labeled PARTIAL_UNIVERSE
        self.assertIn("PARTIAL_UNIVERSE", report["coverage_status"])

        # Check JSON output file exists
        json_path = os.path.join(WORKSPACE, "reports", "egx_universe.json")
        self.assertTrue(os.path.exists(json_path))

    def test_02_every_excluded_security_has_reason(self):
        """
        Verify that no security is dropped without an explicit reason code.
        """
        report = EGXUniverseAuditor.audit_universe("2026-08-20")
        for sec in report["securities"]:
            self.assertIn("status", sec)
            self.assertIn("status_reason", sec)
            if sec["status"] != SecurityStatus.TRADABLE:
                self.assertNotEqual(sec["status_reason"], "")


if __name__ == "__main__":
    unittest.main()
