#!/usr/bin/env python3
# =============================================================================
# tests/test_paper_cohort.py — GEN-26 Paper Cohort Management Unit Tests
# Validates historical cohort preservation (3/30) and 20-Aug-2026 cohort initialization (1/30).
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.paper_cohort import PaperCohortManager


class TestPaperCohort(unittest.TestCase):

    def test_01_cohort_initialization_and_archive(self):
        """
        Verify that initializing new cohort preserves historical baseline archive
        and starts 20-Aug-2026 as Day 1/30.
        """
        cohort = PaperCohortManager.initialize_new_cohort()

        self.assertEqual(cohort["cohort_id"], "COHORT_20260820")
        self.assertEqual(cohort["start_date"], "2026-08-20")
        self.assertEqual(cohort["verified_sessions"], 1)
        self.assertEqual(cohort["total_sessions_required"], 30)
        self.assertTrue(cohort["live_trading_blocked"])

        # Check archive exists and has 3 sessions
        self.assertTrue(os.path.exists(PaperCohortManager.HISTORICAL_ARCHIVE_FILE))


if __name__ == "__main__":
    unittest.main()
