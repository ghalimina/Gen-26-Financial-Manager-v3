#!/usr/bin/env python3
# =============================================================================
# core/independent_backtest_engine.py — Decoupled Independent Execution Engine B
# Standalone Execution Verification Engine for GEN-26 Forensic Compliance
# =============================================================================

import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

# Re-export IndependentBacktester from core.independent_backtester
from core.independent_backtester import IndependentBacktester

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="GEN-26 Engine B Independent Execution Backtester")
    parser.add_argument("--signals", type=str, default=None, help="Path to JSON file containing raw signals")
    parser.add_argument("--holding-days", type=int, default=10, help="Holding period in trading sessions")
    parser.add_argument("--capital", type=float, default=1_000_000.0, help="Initial capital in EGP")

    args = parser.parse_args()

    engine = IndependentBacktester(
        initial_capital_egp=args.capital,
        holding_days=args.holding_days
    )

    if args.signals and os.path.exists(args.signals):
        with open(args.signals, "r", encoding="utf-8") as f:
            signals = json.load(f)
    else:
        # Default institutional test signals
        signals = [
            {"ticker": "COMI.CA", "signal_date": "2024-05-15", "stop_loss_pct": -5.0, "take_profit_pct": 10.0, "score": 85.0},
            {"ticker": "SWDY.CA", "signal_date": "2024-05-15", "stop_loss_pct": -5.0, "take_profit_pct": 10.0, "score": 80.0},
            {"ticker": "TMGH.CA", "signal_date": "2024-05-15", "stop_loss_pct": -5.0, "take_profit_pct": 10.0, "score": 75.0}
        ]

    result = engine.run_backtest_on_signals(signals)
    print(json.dumps(result, ensure_ascii=False, indent=2))
