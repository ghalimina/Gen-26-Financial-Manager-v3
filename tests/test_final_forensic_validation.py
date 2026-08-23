#!/usr/bin/env python3
# =============================================================================
# tests/test_final_forensic_validation.py — Regression Test for Master Forensic Audit
# Verifies that all 25 phases pass and report artifacts are emitted.
# =============================================================================

import os
import json
import unittest
from core.final_forensic_validator import MasterForensicValidator


class TestMasterForensicValidation(unittest.TestCase):
    def test_01_all_25_phases_execute_and_pass(self):
        """Verify that MasterForensicValidator runs cleanly across all 25 phases."""
        results = MasterForensicValidator.run_all()
        self.assertIsNotNone(results)
        self.assertEqual(results["audit_metadata"]["total_phases_executed"], 25)
        self.assertEqual(results["audit_metadata"]["master_verdict"], "FORENSIC_VALIDATION_COMPLETE_TRUTH_VERIFIED")

        # Check Price Truth and Zero Mismatch
        self.assertEqual(results["phase_17_price_consistency"]["status"], "PASS_ZERO_MISMATCH")
        self.assertEqual(results["phase_17_price_consistency"]["price_mismatches_count"], 0)

        # Check Point in Time Anti-Lookahead
        self.assertEqual(results["phase_5_walk_forward_leakage"]["status"], "PASS_ZERO_LEAKAGE")

        # Check Mutation Testing Resilience
        self.assertEqual(results["phase_20_21_mutation_testing"]["status"], "PASS_100_MUTATIONS_CAUGHT")
        self.assertTrue(results["phase_20_21_mutation_testing"]["fault_1_inverted_entry_caught"])
        self.assertTrue(results["phase_20_21_mutation_testing"]["fault_2_allocation_cap_breach_caught"])
        self.assertTrue(results["phase_20_21_mutation_testing"]["fault_3_cash_solvency_breach_caught"])

        # Check Artifact Files Exist
        self.assertTrue(os.path.exists(MasterForensicValidator.JSON_OUTPUT))
        self.assertTrue(os.path.exists(MasterForensicValidator.MD_OUTPUT))


if __name__ == "__main__":
    unittest.main()
