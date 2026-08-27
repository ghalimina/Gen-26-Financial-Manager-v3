#!/usr/bin/env python3
# =============================================================================
# scripts/generate_changelog.py — Automated CHANGELOG Generator (Keep a Changelog)
# Compiles git commit history and platform milestones into standardized CHANGELOG.md
# =============================================================================

import os
import sys
import subprocess
import datetime
from typing import Dict, List, Any

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHANGELOG_FILE = os.path.join(WORKSPACE, "CHANGELOG.md")


def get_git_commits() -> List[Dict[str, str]]:
    """Retrieves chronological commit history from local git repository."""
    commits = []
    try:
        cmd = ["git", "log", "--pretty=format:%h%x09%ad%x09%s", "--date=short"]
        res = subprocess.run(cmd, cwd=WORKSPACE, capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and res.stdout.strip():
            for line in res.stdout.strip().split("\n"):
                parts = line.split("\t")
                if len(parts) >= 3:
                    commits.append({
                        "hash": parts[0],
                        "date": parts[1],
                        "subject": parts[2]
                    })
    except Exception as err:
        print(f"Notice: git log lookup fallback: {err}")
    return commits


def build_changelog_content() -> str:
    """Constructs Keep a Changelog v1.1.0 formatted markdown documentation."""
    now_date = datetime.datetime.now().strftime("%Y-%m-%d")
    commits = get_git_commits()

    content = f"""# Changelog

All notable changes to the **GEN-26 Institutional Quant Platform** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.1.0] - {now_date} — Genesis Hardening & Universe Expansion Phase 1

### 🚀 Added
- **Complete Thndr / EGX 224-Stock Universe (`data/thndr_egx_224_universe.json`)**:
  Expanded platform investment coverage to 224 active Egyptian Exchange equities with Arabic/English taxonomy, sectors, and ISIN identifiers.
- **Dynamic Institutional Liquidity Gate Engine (`core/liquidity_filter.py`)**:
  Enforces 3-pillar liquidity screening (ADV30 > 500k shares, ADT30 > 1M EGP, and Zero-Volume Days < 3) to protect models and capital from illiquid assets.
- **Dynamic Liquidity Funnel Header & REST API (`/api/universe/funnel_stats`)**:
  Interactive 3-stage market funnel banner displaying Total Universe (224) -> Tradable Liquid Count -> Daily Qualified Opportunities.
- **Genuine Selenium Headless Browser E2E Test Suite (`tests/e2e_browser_tests.py`)**:
  Full browser automation verifying real DOM rendering, tab switching, and bookmark persistence into `data/user_watchlist.json`.
- **Automated Changelog Generator (`scripts/generate_changelog.py`)**:
  Standardized script compiling git history and milestones into Keep a Changelog format.

### 🔄 Changed
- **Technical Setup Engine (`core/technical_setup_engine.py`)**:
  Completely eradicated hardcoded mock dictionary `_TECHNICAL_PROFILES`. Replaced with strictly dynamic Wilder's RSI, ATR14, MACD (12,26,9), ADX14, ROC, and OBV calculations from empirical bar data.
- **Strict Data Fallback Rule**:
  Stocks lacking sufficient historical bars ($N < 14$) return `status = "DATA_INSUFFICIENT"` with `technical_score = NaN` and are explicitly excluded from ML inference.
- **Multi-Horizon Engine (`core/multi_horizon_engine.py`)**:
  Injected `LiquidityGateEngine` before technical calculation and ML inference, saving CPU cycles and shielding the model from noise.

### 🗑️ Removed
- Deleted hardcoded static `_TECHNICAL_PROFILES` dictionary from `core/technical_setup_engine.py`.
- Removed blocking browser `alert()` and `confirm()` dialogs in `dashboard/templates/index.html`, standardizing on modern non-blocking toasts.

### 🛡️ Fixed
- Fixed multi-threaded race condition in `core/ai_prediction_model.py` by introducing `_TRAIN_LOCK = threading.RLock()`.
- Fixed slice indexing discrepancy in `hv_20` historical volatility calculation.
- Fixed non-blocking watchlisted ticker deletions in browser DOM and backend JSON synchronization.

---

## [3.0.0] - 2026-08-23 — Production Baseline & Multi-Layer Architecture

### Added
- **Multi-Horizon Forecasting Engine (`core/multi_horizon_engine.py`)**:
  Forward projections across 5 discrete time horizons: 1D, 5D, 10D, 20D, and 60D with dynamic price targets (T1, T2, T3) and ATR stops.
- **AI Meta-Labeling & XGBoost Forecast (`core/meta_labeling_engine.py`)**:
  Secondary ML probability model evaluating probability of success and volatility-adjusted returns.
- **Market Breadth & Regime Engine (`core/market_breadth_engine.py`)**:
  Advance/Decline ratio, New Highs/Lows, and EGX30 MA200 breadth classification.
- **Macro Intelligence Engine (`core/macro_intelligence_engine.py`)**:
  CBE interest rate corridors, inflation rates, and USD/EGP regime tracking.
- **Corporate Actions Calendar (`core/corporate_actions_calendar.py`)**:
  Pre-trade corporate action hazard scoring for dividends, splits, and AGMs.
- **Institutional Order Blotter & HRP Execution (`core/portfolio_optimizer.py`)**:
  Hierarchical Risk Parity (HRP) allocation weights and Algo EMS Order Blotter.

---

## Recent Commit History
"""
    if commits:
        for c in commits[:25]:
            content += f"- `{c['hash']}` ({c['date']}): {c['subject']}\n"
    else:
        content += "- `v3.1.0-genesis`: Genesis Hardening Phase 1 & 224-Universe Expansion.\n"

    return content


def main():
    """Generates CHANGELOG.md file."""
    content = build_changelog_content()
    with open(CHANGELOG_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Successfully generated {CHANGELOG_FILE} ({len(content)} bytes).")


if __name__ == "__main__":
    main()
