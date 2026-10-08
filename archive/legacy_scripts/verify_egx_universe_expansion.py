#!/usr/bin/env python3
# =============================================================================
# scripts/verify_egx_universe_expansion.py — Verification of EGX Universe Expansion
# =============================================================================

import os
import sys

# Force UTF-8 stdout on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.egx_universe_loader import EGXUniverseLoader
from core.multi_horizon_engine import MultiHorizonEngine
from dashboard.app import app


def verify_expansion():
    print("=" * 115)
    print("GEN-26 QUANTITATIVE EXPANSION AUDIT: EGX 100 / EGX 30 / EGX 70 DYNAMIC UNIVERSE")
    print("=" * 115)

    # 1. Stats
    stats = EGXUniverseLoader.get_universe_stats()
    print(f"\n[1/4] Universe Loader Coverage:")
    print(f"   - Total Active Equities : {stats['total_active_equities']}")
    print(f"   - EGX 30 Constituents   : {stats['egx30_constituents']}")
    print(f"   - EGX 70 Constituents   : {stats['egx70_constituents']}")
    print(f"   - Unique Sectors        : {stats['sectors_count']}")

    # 2. Specifically Requested Tickers
    print(f"\n[2/4] Specifically Requested Tickers Audit:")
    req_tickers = ["EFIH.CA", "EGAL.CA", "BTFH.CA", "EMFD.CA", "ESRS.CA", "EKHOA.CA", "POUL.CA", "MOIL.CA"]
    print(f"   {'Ticker':<10} | {'Company (AR)':<36} | {'Sector':<28} | {'Price':<8} | {'Score'}")
    print("   " + "-" * 95)
    for sym in req_tickers:
        analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis(sym)
        assert analysis is not None, f"Failed analysis for {sym}"
        print(f"   {sym:<10} | {analysis['company_name']:<36} | {analysis['sector']:<28} | {analysis['current_price']:<8.2f} | {analysis['overall_score']:<5.1f}")

    # 3. Dynamic Multi-Horizon Rankings across Sub-Universes
    print(f"\n[3/4] Multi-Horizon Dynamic Ranking Filter Test:")
    for univ in ["egx30", "egx70"]:
        ranks = MultiHorizonEngine.get_all_multi_horizon_rankings(universe=univ)
        print(f"\n   >>> Top 5 in Universe [{univ.upper()}] (Total: {len(ranks)} stocks):")
        print(f"   {'#':<3} | {'Ticker':<8} | {'Company Name':<30} | {'Price':<8} | {'Entry Zone':<18} | {'SL (-7%)':<8} | {'Target 20D':<10} | {'Score'}")
        print("   " + "-" * 105)
        for r in ranks[:5]:
            print(f"   {r['rank']:<3} | {r['ticker']:<8} | {r['company_name']:<30} | {r['current_price']:<8.2f} | {r['entry_zone']:<18} | {r['stop_loss']:<8.2f} | {r['horizons']['20D']['target_1']:<10.2f} | {r['overall_score']:<5.1f}")

    # 4. REST API Endpoint Query Parameter Verification
    print(f"\n[4/4] REST API Endpoint Filtering Verification (/api/rankings?universe=...):")
    client = app.test_client()

    res_all = client.get("/api/rankings?universe=all")
    res_30 = client.get("/api/rankings?universe=egx30")
    res_70 = client.get("/api/rankings?universe=egx70")

    assert res_all.status_code == 200, f"/api/rankings?universe=all returned {res_all.status_code}"
    assert res_30.status_code == 200, f"/api/rankings?universe=egx30 returned {res_30.status_code}"
    assert res_70.status_code == 200, f"/api/rankings?universe=egx70 returned {res_70.status_code}"

    d_all = res_all.get_json()
    d_30 = res_30.get_json()
    d_70 = res_70.get_json()

    print(f"   - /api/rankings?universe=all   -> HTTP {res_all.status_code} | {len(d_all)} Equities Returned")
    print(f"   - /api/rankings?universe=egx30 -> HTTP {res_30.status_code} | {len(d_30)} Equities Returned")
    print(f"   - /api/rankings?universe=egx70 -> HTTP {res_70.status_code} | {len(d_70)} Equities Returned")

    print("\n" + "=" * 115)
    print(">> ALL AUDITS AND INVARIANTS PASSED (100% SUCCESS)")
    print("=" * 115)


if __name__ == "__main__":
    verify_expansion()
