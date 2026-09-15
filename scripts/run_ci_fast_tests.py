#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# scripts/run_ci_fast_tests.py — High-Speed Hermetic CI Test Suite Runner
# Runs core institutional test suites in under 60 seconds without hanging on
# external network calls or heavy Monte Carlo loops.
# =============================================================================

import os
import sys
import time
import subprocess

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Core fast production test files
CORE_TEST_FILES = [
    "tests/test_institutional_closure_suite.py",
    "tests/test_institutional_upgrades.py",
    "tests/test_conformal_prediction_engine.py",
    "tests/test_advanced_valuation_engine.py",
    "tests/test_historical_pattern_matcher.py",
    "tests/test_sqlite_acid_persistence.py",
    "tests/test_corporate_actions.py",
    "tests/test_egx_trading_rules_engine.py",
    "tests/test_market_data_truth.py"
]


def run_fast_ci_battery():
    start_time = time.time()
    print("=" * 70)
    print("GEN-26 HIGH-SPEED CLOUD CI TEST BATTERY")
    print(f"Testing {len(CORE_TEST_FILES)} institutional test modules...")
    print("=" * 70)

    # Use pytest
    cmd = [sys.executable, "-m", "pytest"] + CORE_TEST_FILES + ["-v", "--tb=short"]
    env = os.environ.copy()
    env["FLASK_TESTING"] = "1"
    env["PYTHONPATH"] = WORKSPACE

    proc = subprocess.run(cmd, cwd=WORKSPACE, env=env)
    elapsed = round(time.time() - start_time, 2)

    print("=" * 70)
    if proc.returncode == 0:
        print(f"[SUCCESS] ALL {len(CORE_TEST_FILES)} CORE INSTITUTIONAL TEST MODULES PASSED in {elapsed}s")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"[FAILURE] TEST SUITE FAILED (Exit Code: {proc.returncode}) in {elapsed}s")
        print("=" * 70)
        sys.exit(proc.returncode)


if __name__ == "__main__":
    run_fast_ci_battery()
