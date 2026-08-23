#!/usr/bin/env python3
# =============================================================================
# core/paper_observatory.py — GEN-26 Paper Trading Observatory Engine
# Captures immutable state snapshots of every daily paper trading session,
# verifies risk invariants, and exports structured forensic reports.
# =============================================================================

import os
import json
import datetime
from typing import Dict, List, Any, Optional
from core.frozen_invariants import FrozenRiskInvariants


class PaperTradingObservatory:
    """
    Authoritative state capture engine for live paper trading sessions.
    """
    REPORTS_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "reports", "paper_sessions"
    )

    @classmethod
    def record_session(
        cls,
        session_number: int,
        market_date: str,
        market_state: Dict[str, Any],
        universe_state: Dict[str, Any],
        ranking_state: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        execution_state: Dict[str, Any],
        risk_state: Dict[str, Any],
        outcome_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Records a complete, immutable paper trading session snapshot.
        """
        os.makedirs(cls.REPORTS_DIR, exist_ok=True)
        session_id = f"SESS-{market_date.replace('-', '')}-{session_number:02d}"
        timestamp = datetime.datetime.now().isoformat()

        # Invariant Verification Audit
        cash_solvency = risk_state.get("cash_after", 0.0) >= 0.0
        stock_alloc_ratio = risk_state.get("stock_allocation_pct", 0.0) / 100.0
        allocation_safe = stock_alloc_ratio <= (FrozenRiskInvariants.MAX_TOTAL_STOCK_ALLOCATION_PCT + 1e-4)
        cash_reserve_safe = (1.0 - stock_alloc_ratio) >= (FrozenRiskInvariants.MANDATORY_CASH_RESERVE_PCT - 1e-4)

        risk_incidents = []
        if not cash_solvency:
            risk_incidents.append("CASH_SOLVENCY_BREACH")
        if not allocation_safe:
            risk_incidents.append("ALLOCATION_CAP_BREACH")
        if not cash_reserve_safe:
            risk_incidents.append("CASH_RESERVE_BREACH")

        session_status = "RISK_FAILURE" if risk_incidents else "VERIFIED_PASS"

        session_payload = {
            "session_metadata": {
                "session_id": session_id,
                "session_number": session_number,
                "market_date": market_date,
                "timestamp": timestamp,
                "engine_version": "3.0.0",
                "status": session_status,
                "risk_incidents": risk_incidents
            },
            "market_state": market_state,
            "universe": universe_state,
            "ranking": ranking_state,
            "portfolio": portfolio_state,
            "execution": execution_state,
            "risk": risk_state,
            "outcome": outcome_state
        }

        # Export JSON
        json_path = os.path.join(cls.REPORTS_DIR, f"session_{session_number:02d}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(session_payload, f, ensure_ascii=False, indent=2)

        # Export Markdown
        md_path = os.path.join(cls.REPORTS_DIR, f"session_{session_number:02d}.md")
        cls._export_markdown_report(session_payload, md_path)

        return session_payload

    @classmethod
    def _export_markdown_report(cls, payload: Dict[str, Any], filepath: str):
        """Generates a human-readable markdown forensic report for the session."""
        meta = payload["session_metadata"]
        mkt = payload["market_state"]
        univ = payload["universe"]
        port = payload["portfolio"]
        risk = payload["risk"]
        out = payload["outcome"]

        md_content = f"""# 🏛️ GEN-26 PAPER TRADING SESSION #{meta['session_number']:02d}

**Session ID:** `{meta['session_id']}`  
**Market Date:** `{meta['market_date']}`  
**Timestamp:** `{meta['timestamp']}`  
**Session Status:** `{meta['status']}`  

---

## 1. Market State & Regime
- **Market Regime:** `{mkt.get('regime', 'UNKNOWN')}`
- **Trailing Breadth (Advance Ratio):** `{mkt.get('breadth_advance_pct', 50.0):.1f}%`
- **Data Health:** `{mkt.get('data_health', 'PASS')}`

## 2. Tradable Universe & Ranking
- **Total Universe Candidates:** `{univ.get('total_candidates', 27)}`
- **Tradable Assets:** `{univ.get('tradable_count', 27)}`
- **Excluded Assets:** `{univ.get('excluded_count', 0)}` ({univ.get('exclusion_reasons', 'None')})

## 3. Portfolio Allocation & Sizing
- **Invested Stock Allocation:** `{risk.get('stock_allocation_pct', 0.0):.1f}%` (Max Allowed: 65.0%)
- **Free Cash Reserve:** `{risk.get('cash_reserve_pct', 100.0):.1f}%` (Min Required: 35.0%)
- **Total Portfolio Equity:** `{risk.get('equity_after', 100000.0):,.2f} EGP`
- **Allocated Orders:** `{len(port.get('allocated_orders', []))}`

## 4. Execution & Risk Audit
- **Cash Solvency:** `{'PASS' if risk.get('cash_after', 0.0) >= 0.0 else 'FAIL'}`
- **Simulated Realized P&L:** `{out.get('realized_pnl_egp', 0.0):+,.2f} EGP`
- **Unrealized P&L:** `{out.get('unrealized_pnl_egp', 0.0):+,.2f} EGP`
- **Benchmark (EGX30) Return:** `{out.get('benchmark_return_pct', 0.0):+.2f}%`
- **Risk Incidents:** `{', '.join(meta['risk_incidents']) if meta['risk_incidents'] else 'None (Clean Run)'}`
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
