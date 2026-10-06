#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_zenith_optimization_convergence.py — End-to-End Convergence Test Suite
Verifies:
1. Master Alpha Synthesizer & Golden Consensus Filter.
2. Self-learning MLOps Recalibration & 48-Hour Cooling-Off (Episodic Memory).
3. Thndr Actionable Decision Hub (/api/thndr_daily_card) & Smart Cash Radar.
4. Real Portfolio CRUD & Cash Balance endpoints.
5. EOD Telegram Dispatch formatting.
"""

import os
import sys
import json
import pytest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.trade_selection_model import TradeSelectionModel
from core.trade_post_mortem_engine import TradePostMortemEngine
from core.mlops_pipeline import MLOpsPipeline
from core.unified_pipeline_orchestrator import UnifiedPipelineOrchestrator
from core.real_portfolio import RealPortfolioTracker
from dashboard.app import app


def test_01_golden_consensus_filter_logic():
    """Verifies all gates of the Golden Consensus Filter."""
    theories_pass = {
        "theories": {
            "wyckoff": {"score": 85.0},
            "smart_money": {"score": 90.0},
            "minervini_vcp": {"score": 88.0},
            "can_slim": {"score": 82.0},
            "dow_theory": {"score": 60.0},
            "elliott_wave": {"score": 50.0}
        }
    }
    # 4/6 pass, DQS=90, GDR spread=+1.5%, Bull=True, NetReturn=3.5%, No cooling-off
    res = TradeSelectionModel.evaluate_golden_consensus(
        ticker="TEST.CA",
        current_price=100.0,
        theories_result=theories_pass,
        dqs_score=90.0,
        gdr_spread_pct=1.5,
        is_market_bull=True,
        expected_net_return_pct=3.5,
        cooling_off_active=False
    )
    assert res["is_golden_consensus"] is True
    assert res["consensus_verdict"] == "STRONG_BUY"
    assert res["gates"]["theories_gate_passed"] is True
    assert res["gates"]["dqs_gate_passed"] is True
    assert res["gates"]["gdr_gate_passed"] is True

    # If London GDR trades at -3.5% discount, Golden Consensus must block STRONG_BUY
    res_gdr_threat = TradeSelectionModel.evaluate_golden_consensus(
        ticker="TEST.CA",
        current_price=100.0,
        theories_result=theories_pass,
        dqs_score=90.0,
        gdr_spread_pct=-3.5,
        is_market_bull=True,
        expected_net_return_pct=3.5,
        cooling_off_active=False
    )
    assert res_gdr_threat["is_golden_consensus"] is False
    assert res_gdr_threat["gates"]["gdr_gate_passed"] is False


def test_02_episodic_memory_cooling_off():
    """Verifies that hitting stop loss triggers automatic 48h cooling-off lock."""
    ticker = "COOL_TEST.CA"
    TradePostMortemEngine.clear_cooling_off(ticker)
    assert TradePostMortemEngine.is_ticker_in_cooling_off(ticker)[0] is False

    # Register stop loss hit
    lock_info = TradePostMortemEngine.register_stop_loss_hit(
        ticker=ticker,
        reason="Test Stop Loss Hit",
        lock_hours=48
    )
    assert lock_info["is_active"] is True

    # Now verify ticker is locked
    is_locked, rem_hrs, reason = TradePostMortemEngine.is_ticker_in_cooling_off(ticker)
    assert is_locked is True
    assert rem_hrs > 40.0

    # Cleanup
    TradePostMortemEngine.clear_cooling_off(ticker)
    assert TradePostMortemEngine.is_ticker_in_cooling_off(ticker)[0] is False


def test_03_mlops_adaptive_recalibration_audit():
    """Verifies weekly adaptive recalibration executes without regression."""
    audit = MLOpsPipeline.run_adaptive_recalibration_audit(window_days=30)
    assert "brier_score" in audit
    assert "expected_calibration_error" in audit
    assert "hit_rate_pct" in audit
    assert "recalibration_action" in audit


def test_04_thndr_daily_card_endpoint():
    """Verifies /api/thndr_daily_card REST endpoint returns full schema."""
    with app.test_client() as client:
        resp = client.get("/api/thndr_daily_card")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "SUCCESS"
        assert "thndr_daily_card" in data
        assert "smart_cash_radar" in data

        card = data["thndr_daily_card"]
        assert "ticker" in card
        assert "opening_auction_price" in card
        assert "stop_loss_price" in card
        assert "target_1_price" in card
        assert "suggested_shares" in card
        assert "breakeven_rule_ar" in card

        radar = data["smart_cash_radar"]
        assert radar["mandatory_cash_floor_pct"] == 35.0
        assert len(radar["recommended_funds"]) >= 2


def test_05_real_portfolio_crud_and_cash_api():
    """Verifies that real portfolio CRUD and cash endpoints mutate data cleanly."""
    with app.test_client() as client:
        # 1. Update cash
        resp_cash = client.post("/api/real_portfolio/cash", json={"cash_egp": 85000.0})
        assert resp_cash.status_code in (200, 201)

        # 2. Add holding
        resp_add = client.post("/api/real_portfolio/add", json={
            "ticker": "ETEL.CA",
            "quantity": 100,
            "average_entry_price": 32.50,
            "manual_notes": "Zenith Unit Test"
        })
        # If already exists, delete first then add
        if resp_add.status_code != 200:
            client.post("/api/real_portfolio/delete", json={"ticker": "ETEL.CA", "confirm": True})
            resp_add = client.post("/api/real_portfolio/add", json={
                "ticker": "ETEL.CA",
                "quantity": 100,
                "average_entry_price": 32.50,
                "manual_notes": "Zenith Unit Test"
            })
        assert resp_add.status_code == 200

        # 3. Edit holding
        resp_edit = client.post("/api/real_portfolio/edit", json={
            "ticker": "ETEL.CA",
            "quantity": 120,
            "average_entry_price": 33.00,
            "manual_notes": "Zenith Unit Test Edited"
        })
        assert resp_edit.status_code == 200

        # 4. Delete holding
        resp_del = client.post("/api/real_portfolio/delete", json={
            "ticker": "ETEL.CA",
            "confirm": True
        })
        assert resp_del.status_code == 200


def test_06_eod_telegram_report_formatting():
    """Verifies that EOD report formats Thndr Card and alerts into clean message."""
    import scripts.send_eod_telegram_report as r
    regime_data = {"regime": "STRONG_BULL", "cash_reserve_pct": 35.0}
    macro_data = {"indicators": {"usd_egp_rate": {"value": 52.38}, "brent_oil_usd": {"value": 75.0}, "gold_usd_oz": {"value": 2650.0}}}
    top_stocks = [{"ticker": "SWDY.CA", "company_name": "السويدي إليكتريك", "current_price": 118.0, "overall_score": 90.0, "decision": "STRONG_BUY"}]

    messages = r.build_concise_reports(regime_data, macro_data, top_stocks)
    assert len(messages) >= 1
    assert "GEN-26" in messages[0]
    assert "EGX30" in messages[0]
