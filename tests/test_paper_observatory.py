#!/usr/bin/env python3
# =============================================================================
# tests/test_paper_observatory.py — GEN-26 Paper Trading Observatory Tests
# Validates Paper Observatory state capture, immutable snapshots, replay determinism,
# reality auditing, and multi-dimensional drift monitoring.
# =============================================================================

import unittest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.paper_observatory import PaperTradingObservatory
from core.decision_snapshot import ImmutableDecisionSnapshotStore
from core.paper_reality_audit import PaperRealityAuditor
from core.drift_monitor import PlatformDriftMonitor


class TestPaperObservatory(unittest.TestCase):

    def test_01_session_recording_and_artifact_export(self):
        """
        Verify that recording a paper trading session produces valid JSON & Markdown reports.
        """
        market_state = {"regime": "BULL_MOMENTUM", "breadth_advance_pct": 65.0, "data_health": "PASS"}
        univ_state = {"total_candidates": 27, "tradable_count": 27, "excluded_count": 0}
        rank_state = {"top_candidates": ["COMI.CA", "SWDY.CA"]}
        port_state = {"allocated_orders": [{"ticker": "COMI.CA", "shares": 100}]}
        exec_state = {"fills": [{"ticker": "COMI.CA", "fill_price": 100.10}]}
        risk_state = {"cash_after": 50_000.0, "stock_allocation_pct": 50.0, "equity_after": 100_000.0}
        out_state = {"realized_pnl_egp": 1200.0, "unrealized_pnl_egp": 800.0, "benchmark_return_pct": 0.85}

        sess = PaperTradingObservatory.record_session(
            session_number=99,
            market_date="2026-08-20",
            market_state=market_state,
            universe_state=univ_state,
            ranking_state=rank_state,
            portfolio_state=port_state,
            execution_state=exec_state,
            risk_state=risk_state,
            outcome_state=out_state
        )

        self.assertEqual(sess["session_metadata"]["status"], "VERIFIED_PASS")
        self.assertEqual(len(sess["session_metadata"]["risk_incidents"]), 0)

        # Verify files exist on disk
        json_path = os.path.join(PaperTradingObservatory.REPORTS_DIR, "session_99.json")
        md_path = os.path.join(PaperTradingObservatory.REPORTS_DIR, "session_99.md")
        self.assertTrue(os.path.exists(json_path))
        self.assertTrue(os.path.exists(md_path))

    def test_02_risk_incident_detection(self):
        """
        Verify that breaching stock allocation cap (>65%) flags RISK_FAILURE.
        """
        market_state = {"regime": "BULL_MOMENTUM", "breadth_advance_pct": 65.0, "data_health": "PASS"}
        risk_state_breach = {"cash_after": 20_000.0, "stock_allocation_pct": 80.0, "equity_after": 100_000.0}

        sess = PaperTradingObservatory.record_session(
            session_number=98,
            market_date="2026-08-20",
            market_state=market_state,
            universe_state={},
            ranking_state={},
            portfolio_state={},
            execution_state={},
            risk_state=risk_state_breach,
            outcome_state={}
        )

        self.assertEqual(sess["session_metadata"]["status"], "RISK_FAILURE")
        self.assertIn("ALLOCATION_CAP_BREACH", sess["session_metadata"]["risk_incidents"])

    def test_03_immutable_decision_snapshot_and_replay(self):
        """
        Verify that decision snapshots are saved with SHA256 integrity hash and deterministically replayed.
        """
        dec_id = "DEC_TEST_REPLAY_001"
        ImmutableDecisionSnapshotStore.save_snapshot(
            decision_id=dec_id,
            session_id="SESS-20260820-01",
            ticker="COMI.CA",
            decision_object={"action": "BUY LIMIT", "entry": 100.0},
            market_state={"regime": "BULL_MOMENTUM"},
            features_snapshot={"mom_20d": 0.15, "roe": 22.5},
            ranking_snapshot={"rank": 1, "alpha_score": 88.0},
            risk_evaluation={"risk_score": 85.0, "reasons": []},
            portfolio_state={"weight": 0.10}
        )

        # Replay
        replayed = ImmutableDecisionSnapshotStore.replay_decision(dec_id)
        self.assertIsNotNone(replayed)
        self.assertEqual(replayed["snapshot_metadata"]["ticker"], "COMI.CA")
        self.assertEqual(replayed["decision"]["action"], "BUY LIMIT")
        self.assertIn("integrity_hash", replayed["snapshot_metadata"])

    def test_04_paper_reality_auditor(self):
        """
        Verify that PaperRealityAuditor evaluates paper statistics and flags sample confidence.
        """
        audit = PaperRealityAuditor.audit_session_reality(
            total_sessions_recorded=3,
            realized_trade_returns_pct=[4.5, 3.2, -1.8],
            slippage_records_pct=[0.10, 0.10]
        )

        self.assertEqual(audit["sessions_completed"], 3)
        self.assertEqual(audit["statistical_power"], "LOW")
        self.assertEqual(audit["execution_realism"]["status"], "PASS")
        self.assertEqual(audit["overall_reality_verdict"], "HEALTHY_ALIGNMENT")

    def test_05_platform_drift_monitor(self):
        """
        Verify drift monitor detects warning state when slippage widens or data health degrades.
        """
        # Normal
        drift_norm = PlatformDriftMonitor.evaluate_all_drifts(
            data_health="PASS",
            current_mean_slippage_pct=0.10,
            benchmark_slippage_pct=0.10
        )
        self.assertEqual(drift_norm["overall_drift_status"], "STABLE")

        # High slippage drift
        drift_high_slip = PlatformDriftMonitor.evaluate_all_drifts(
            data_health="PASS",
            current_mean_slippage_pct=0.30, # 3x benchmark
            benchmark_slippage_pct=0.10
        )
        self.assertEqual(drift_high_slip["overall_drift_status"], "WARNING")
        self.assertEqual(drift_high_slip["dimensions"]["EXECUTION_DRIFT"], "WARNING")


if __name__ == "__main__":
    unittest.main()
