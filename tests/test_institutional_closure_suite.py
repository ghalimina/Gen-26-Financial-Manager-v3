#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_institutional_closure_suite.py
# Verification suite for the entire institutional quant stack closure:
# 1. TradePostMortemEngine (Reflexion loop & root cause classification)
# 2. EpisodicTradeMemory (Cosine similarity retrieval & proactive trade veto)
# 3. AlphaFactorMutator (Evolutionary factor mutation & walk-forward fitness)
# 4. DualLoopOrchestrator (Fast intraday vs Slow post-market cycles)
# 5. FixBrokerGateway (FIX 4.4 tag-value encoding, checksum, DMA order states)
# 6. OrderBookVpinEngine (LOB Level 2 depth, Micro-price & VPIN toxicity)
# 7. SmartOrderRouter (VWAP & Almgren-Chriss optimal impact slicing)
# 8. McdrTaxEngine (T+0/T+2 clearing, 10% CGT, Tax-Loss Harvesting)
# 9. AdvancedFeatureEngineering (Camarilla, CMF, MFI, Gap Typology)
# =============================================================================

import pytest
import os
import sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.trade_post_mortem_engine import TradePostMortemEngine
from core.episodic_trade_memory import EpisodicTradeMemory
from core.alpha_factor_mutator import AlphaFactorMutator
from core.dual_loop_orchestrator import DualLoopOrchestrator
from core.fix_broker_gateway import FixBrokerGateway, SOH
from core.order_book_vpin_engine import OrderBookVpinEngine
from core.smart_order_router import SmartOrderRouter
from core.mcdr_tax_engine import McdrTaxEngine
from core.advanced_feature_engineering import AdvancedFeatureEngineering


def test_trade_post_mortem_bull_trap():
    """Verifies that low volume + negative CMF triggers BULL_TRAP_LOW_VOLUME diagnosis."""
    report = TradePostMortemEngine.diagnose_trade(
        ticker="COMI",
        entry_price=85.0,
        exit_price=81.0,
        entry_features={"volume_ratio": 0.60, "cmf": -0.15, "mfi": 55.0, "adx": 22.0, "spread_pct": 0.25},
        exit_reason="STOP_LOSS"
    )
    assert report.failure_category == "BULL_TRAP_LOW_VOLUME"
    assert "volume_ratio" in report.culprit_factors
    assert "cmf" in report.culprit_factors
    assert report.realized_pnl_pct < 0.0
    assert "حظر الشراء" in report.actionable_rule_ar


def test_trade_post_mortem_exhaustion():
    """Verifies that extreme high MFI triggers EXHAUSTION_REVERSAL diagnosis."""
    report = TradePostMortemEngine.diagnose_trade(
        ticker="FWRY",
        entry_price=6.50,
        exit_price=6.10,
        entry_features={"volume_ratio": 1.2, "cmf": 0.10, "mfi": 85.0, "adx": 28.0, "spread_pct": 0.30},
        exit_reason="STOP_LOSS"
    )
    assert report.failure_category == "EXHAUSTION_REVERSAL"
    assert "mfi" in report.culprit_factors


def test_episodic_trade_memory_retrieval_and_veto():
    """Verifies cosine similarity encoding and proactive trade veto on historical failure match."""
    vec1 = EpisodicTradeMemory.encode_feature_vector({"volume_ratio": 0.60, "cmf": -0.15, "mfi": 50.0, "adx": 20.0, "spread_pct": 0.30})
    vec2 = EpisodicTradeMemory.encode_feature_vector({"volume_ratio": 0.62, "cmf": -0.14, "mfi": 52.0, "adx": 21.0, "spread_pct": 0.32})
    sim = EpisodicTradeMemory.cosine_similarity(vec1, vec2)
    assert sim > 0.95

    # Test candidate evaluation
    eval_res = EpisodicTradeMemory.evaluate_trade_candidate(
        ticker="COMI",
        current_features={"volume_ratio": 1.40, "cmf": 0.22, "mfi": 55.0, "adx": 30.0, "spread_pct": 0.20},
        regime="BULL_TREND"
    )
    assert "safe_to_trade" in eval_res
    assert isinstance(eval_res["safe_to_trade"], bool)


def test_alpha_factor_mutator_evolution():
    """Verifies that AlphaFactorMutator mutates gene expressions and evaluates walk-forward fitness."""
    candidates = AlphaFactorMutator.evolve_generation(population_size=2, regime="BULL_TREND")
    assert len(candidates) == 2
    for cand in candidates:
        assert "fitness_score" in cand
        assert "oos_sharpe" in cand
        assert "expression" in cand
        assert cand["fitness_score"] >= 0.0


def test_dual_loop_orchestrator():
    """Verifies fast intraday screen and slow post-market evolution cycle."""
    fast_eval = DualLoopOrchestrator.fast_loop_screen_candidate(
        ticker="SWDY",
        current_features={"volume_ratio": 1.1, "cmf": 0.15, "mfi": 60.0, "adx": 26.0, "spread_pct": 0.25}
    )
    assert "safe_to_trade" in fast_eval

    slow_res = DualLoopOrchestrator.run_post_market_evolution_cycle(
        closed_trades=[
            {
                "ticker": "EAST",
                "entry_price": 28.0,
                "exit_price": 26.5,
                "entry_features": {"volume_ratio": 0.70, "cmf": -0.10, "mfi": 50.0, "adx": 20.0, "spread_pct": 0.30},
                "exit_reason": "STOP_LOSS",
                "holding_period_days": 2,
                "slippage_pct": 0.15
            }
        ]
    )
    assert slow_res["cycle_status"] == "COMPLETED"
    assert slow_res["trades_diagnosed_count"] >= 1
    assert "compiled_policy" in slow_res


def test_fix_broker_gateway_lifecycle():
    """Verifies FIX 4.4 message formatting, checksum calculation, and execution flow."""
    gw = FixBrokerGateway(sender_comp_id="TEST_FUND", target_comp_id="HERMES_DMA")
    logon_msg = gw.logon()
    assert "35=A" in logon_msg
    assert "10=" in logon_msg
    assert gw.is_logged_on is True

    # Checksum verification
    parsed = gw.parse_fix_message(logon_msg)
    assert parsed[35] == "A"
    assert parsed[49] == "TEST_FUND"

    # NewOrderSingle
    order = gw.send_new_order_single("COMI.CA", side="BUY", quantity=1000, price=84.50)
    assert order["order_status"] == "NEW"
    assert order["quantity"] == 1000

    # Simulate ExecutionReport
    exec_rep = gw.simulate_broker_execution(order["cl_ord_id"], fill_price=84.45, fill_pct=1.0)
    assert exec_rep["order_status"] == "FILLED"
    assert exec_rep["cum_qty"] == 1000
    assert exec_rep["avg_px"] == 84.45
    assert "35=8" in exec_rep["raw_execution_report"]


def test_order_book_vpin_and_depth():
    """Verifies LOB depth micro-price and VPIN toxicity calculations."""
    bids = [(84.50, 10000), (84.45, 15000), (84.40, 20000)]
    asks = [(84.60, 5000), (84.65, 8000), (84.70, 12000)]

    depth = OrderBookVpinEngine.analyze_order_book_depth(bids, asks)
    assert depth["valid"] is True
    assert depth["best_bid"] == 84.50
    assert depth["best_ask"] == 84.60
    assert depth["spread"] == 0.10
    assert depth["micro_price"] > 84.50
    assert depth["pressure"] == "BUY_PRESSURE"  # More bid depth than ask

    # VPIN Toxicity test
    sizes = [10000, 15000, 20000, 12000, 18000, 25000]
    prices = [84.50, 84.60, 84.70, 84.65, 84.75, 84.80]
    vpin_res = OrderBookVpinEngine.calculate_vpin(sizes, prices, bucket_volume=20000, num_buckets=3)
    assert "vpin" in vpin_res
    assert 0.0 <= vpin_res["vpin"] <= 1.0


def test_smart_order_router_vwap_and_almgren_chriss():
    """Verifies VWAP volume profile slicing and Almgren-Chriss optimal trajectory."""
    vwap_slices = SmartOrderRouter.generate_vwap_schedule(total_quantity=9000, symbol="HRHO.CA")
    assert len(vwap_slices) == 9
    tot_shares = sum(s["slice_quantity"] for s in vwap_slices)
    assert tot_shares == 9000

    ac_res = SmartOrderRouter.generate_almgren_chriss_schedule(total_shares=50000, num_intervals=5)
    assert ac_res["total_shares"] == 50000
    assert len(ac_res["execution_slices"]) == 5
    assert sum(ac_res["execution_slices"]) == 50000
    assert ac_res["estimated_impact_bps"] > 0.0


def test_mcdr_tax_engine():
    """Verifies MCDR settlement cycles, 10% CGT, and tax-loss harvesting."""
    settle = McdrTaxEngine.calculate_trade_settlement(
        symbol="COMI",
        trade_date="2026-09-07",
        shares=1000,
        price=85.0,
        is_list_a=True,
        is_same_day_trade=True
    )
    assert settle["settlement_cycle"] == "T+0"
    assert settle["mcdr_clearing_fee"] > 0

    cgt_res = McdrTaxEngine.compute_fiscal_year_cgt([
        {"realized_pnl_egp": 50000.0},
        {"realized_pnl_egp": -10000.0}
    ])
    assert cgt_res["net_realized_pnl_egp"] == 40000.0
    assert cgt_res["estimated_cgt_liability_egp"] == 4000.0  # 10% of 40,000

    harvest = McdrTaxEngine.scan_tax_loss_harvesting_opportunities([
        {"symbol": "COMI", "shares": 500, "avg_cost": 90.0, "current_price": 82.0}
    ])
    assert len(harvest) == 1
    assert harvest[0]["potential_tax_shield_egp"] == (8.0 * 500) * 0.10


def test_advanced_feature_engineering_camarilla_cmf_mfi_gap():
    """Verifies Camarilla pivots, Chaikin Money Flow, MFI, and Gap classification."""
    pivots = AdvancedFeatureEngineering.calculate_camarilla_pivots(high=86.0, low=83.0, close=85.0)
    assert pivots["h4_breakout"] > pivots["h3_reversal"]
    assert pivots["l3_reversal"] > pivots["l4_breakdown"]

    highs = [82, 83, 84, 85, 86]
    lows = [80, 81, 82, 83, 84]
    closes = [81.5, 82.5, 83.8, 84.9, 85.8]
    vols = [1000, 1500, 2000, 1800, 2500]

    cmf = AdvancedFeatureEngineering.calculate_chaikin_money_flow(highs, lows, closes, vols, window=5)
    assert isinstance(cmf, float)
    assert -1.0 <= cmf <= 1.0

    mfi = AdvancedFeatureEngineering.calculate_money_flow_index(highs, lows, closes, vols, window=4)
    assert isinstance(mfi, float)
    assert 0.0 <= mfi <= 100.0

    gap = AdvancedFeatureEngineering.classify_price_gap(
        prev_close=80.0,
        open_price=83.0,
        volume=50000,
        avg_volume=20000,
        atr=2.0
    )
    assert gap["gap_type"] == "BREAKAWAY"
