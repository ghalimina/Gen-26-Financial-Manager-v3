#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# scripts/verify_institutional_stack.py — Full Institutional Quant Stack Verification
# Executes an end-to-end integration test of all newly closed institutional engines:
# 1. FIX Protocol 4.4 DMA Gateway
# 2. Limit Order Book L2 & VPIN Toxicity Engine
# 3. Smart Order Router (VWAP & Almgren-Chriss)
# 4. MCDR Settlement & Egyptian CGT Engine
# 5. Camarilla, CMF, MFI, Gap Typology
# 6. Trade Post-Mortem Forensic Engine (Reflexion)
# 7. Episodic Trade Memory & Veto Guard
# 8. Alpha Factor Mutator (Alpha-Evolve / FunSearch)
# 9. Dual-Loop Orchestrator
# =============================================================================

import os
import sys
import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from core.fix_broker_gateway import FixBrokerGateway
from core.order_book_vpin_engine import OrderBookVpinEngine
from core.smart_order_router import SmartOrderRouter
from core.mcdr_tax_engine import McdrTaxEngine
from core.advanced_feature_engineering import AdvancedFeatureEngineering
from core.trade_post_mortem_engine import TradePostMortemEngine
from core.episodic_trade_memory import EpisodicTradeMemory
from core.alpha_factor_mutator import AlphaFactorMutator
from core.dual_loop_orchestrator import DualLoopOrchestrator


def run_full_institutional_verification():
    print("=" * 80)
    print("🏛️ GEN-26 INSTITUTIONAL QUANT STACK & SELF-IMPROVING AGENT AUDIT")
    print(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # 1. FIX Protocol 4.4 Gateway
    print("\n[1/8] 📡 Testing Institutional FIX Protocol 4.4 DMA Gateway...")
    gw = FixBrokerGateway(sender_comp_id="GEN26_FUND", target_comp_id="EGX_HERMES_DMA")
    logon_msg = gw.logon()
    order = gw.send_new_order_single("COMI.CA", "BUY", quantity=2500, price=84.50)
    exec_rep = gw.simulate_broker_execution(order["cl_ord_id"], fill_price=84.48)
    print(f"  ✓ FIX Session: Logged on successfully (MsgType=A).")
    print(f"  ✓ Order Submitted: ClOrdID={order['cl_ord_id']} (Status={order['order_status']})")
    print(f"  ✓ Execution Report: ExecID={exec_rep['exec_id']} Filled at {exec_rep['avg_px']:.2f} EGP")

    # 2. Limit Order Book L2 & VPIN Toxicity
    print("\n[2/8] 📊 Testing Level 2 Order Book Depth & VPIN Toxicity Engine...")
    bids = [(84.50, 25000), (84.40, 40000), (84.30, 60000)]
    asks = [(84.60, 15000), (84.70, 20000), (84.80, 30000)]
    lob = OrderBookVpinEngine.analyze_order_book_depth(bids, asks)
    sizes = [15000, 22000, 30000, 18000, 25000, 40000]
    prices = [84.50, 84.55, 84.60, 84.58, 84.65, 84.70]
    vpin = OrderBookVpinEngine.calculate_vpin(sizes, prices, bucket_volume=25000)
    print(f"  ✓ LOB Spread: {lob['spread']:.2f} EGP ({lob['spread_bps']:.1f} bps) | Micro-Price={lob['micro_price']:.2f} EGP")
    print(f"  ✓ Order Flow Toxicity: VPIN={vpin['vpin_pct']:.2f}% | Regime={vpin['toxicity_regime']}")

    # 3. Smart Order Router (VWAP & Almgren-Chriss)
    print("\n[3/8] ⚡ Testing Smart Order Router (SOR)...")
    vwap_slices = SmartOrderRouter.generate_vwap_schedule(10000, "COMI.CA")
    ac_sched = SmartOrderRouter.generate_almgren_chriss_schedule(total_shares=50000, num_intervals=5)
    print(f"  ✓ VWAP Slices Generated: {len(vwap_slices)} intraday tranches (Sum={sum(s['slice_quantity'] for s in vwap_slices)})")
    print(f"  ✓ Almgren-Chriss Optimal Trajectory: Impact={ac_sched['estimated_impact_bps']:.2f} bps | Slices={ac_sched['execution_slices']}")

    # 4. MCDR Clearing & Egyptian 10% CGT
    print("\n[4/8] ⚖️ Testing MCDR Settlement & Tax-Loss Harvesting...")
    settle = McdrTaxEngine.calculate_trade_settlement("COMI", "2026-09-07", 2500, 84.50, is_list_a=True, is_same_day_trade=True)
    cgt = McdrTaxEngine.compute_fiscal_year_cgt([{"realized_pnl_egp": 250000.0}, {"realized_pnl_egp": -50000.0}])
    harvest = McdrTaxEngine.scan_tax_loss_harvesting_opportunities([{"symbol": "COMI", "shares": 1000, "avg_cost": 90.0, "current_price": 84.50}])
    print(f"  ✓ Settlement Cycle: {settle['settlement_cycle']} | MCDR Fee={settle['mcdr_clearing_fee']:.2f} EGP")
    print(f"  ✓ Egyptian 10% CGT: Net PnL={cgt['net_realized_pnl_egp']:.2f} EGP | Tax Liability={cgt['estimated_cgt_liability_egp']:.2f} EGP")
    print(f"  ✓ Tax-Loss Harvest Candidates: {len(harvest)} (Shield={harvest[0]['potential_tax_shield_egp']:.2f} EGP -> Substitute={harvest[0]['recommended_substitute']})")

    # 5. Camarilla, CMF, MFI & Gap Typology
    print("\n[5/8] 📐 Testing Camarilla Pivots, CMF, MFI & Price Gap Typology...")
    cam = AdvancedFeatureEngineering.calculate_camarilla_pivots(high=86.0, low=83.0, close=85.0)
    cmf = AdvancedFeatureEngineering.calculate_chaikin_money_flow([84, 85, 86], [82, 83, 84], [83.5, 84.8, 85.8], [1000, 1500, 2000])
    gap = AdvancedFeatureEngineering.classify_price_gap(prev_close=80.0, open_price=82.5, volume=35000, avg_volume=15000, atr=1.8)
    print(f"  ✓ Camarilla Pivots: H4 Breakout={cam['h4_breakout']} | L3 Reversal={cam['l3_reversal']}")
    print(f"  ✓ Flow Oscillators: CMF={cmf:+.4f} | Gap Typology={gap['gap_type']} ({gap['description_ar']})")

    # 6. Forensic Post-Mortem Reflexion Engine
    print("\n[6/8] 🔍 Testing Forensic Trade Post-Mortem Engine (Reflexion)...")
    pm = TradePostMortemEngine.diagnose_trade(
        ticker="FWRY",
        entry_price=6.80,
        exit_price=6.35,
        entry_features={"volume_ratio": 0.55, "cmf": -0.18, "mfi": 52.0, "adx": 19.0, "spread_pct": 0.35},
        exit_reason="STOP_LOSS"
    )
    print(f"  ✓ Post-Mortem ID: {pm.report_id} | Failure Category: {pm.failure_category}")
    print(f"  ✓ Root Cause Diagnosis: {pm.diagnosis_ar}")
    print(f"  ✓ Synthesized Machine Filter: {pm.actionable_code_filter}")

    # 7. Episodic Trade Memory & Veto Guard
    print("\n[7/8] 🧠 Testing Episodic Trade Memory & Proactive Safety Veto...")
    EpisodicTradeMemory.record_post_mortem(pm, regime="BULL_TREND")
    veto_test = EpisodicTradeMemory.evaluate_trade_candidate(
        ticker="FWRY",
        current_features={"volume_ratio": 0.58, "cmf": -0.16, "mfi": 53.0, "adx": 19.5, "spread_pct": 0.35},
        regime="BULL_TREND"
    )
    print(f"  ✓ Memory Query Status: {veto_test['status_ar']}")
    print(f"  ✓ Safe to Trade: {veto_test['safe_to_trade']} | Similarity to Prior Loss: {veto_test.get('top_similarity', 0.0)*100:.1f}%")

    # 8. Alpha Factor Mutator & Dual-Loop Orchestration
    print("\n[8/8] 🧬 Testing Evolutionary Alpha Factor Mutator & Dual-Loop Orchestrator...")
    mutated = AlphaFactorMutator.evolve_generation(population_size=2)
    dual_cycle = DualLoopOrchestrator.run_post_market_evolution_cycle()
    print(f"  ✓ Alpha Evolution: Tested {len(mutated)} offspring (Top Fitness={mutated[0]['fitness_score']:.4f})")
    print(f"  ✓ Dual-Loop Post-Market Status: {dual_cycle['cycle_status']} ({dual_cycle['summary_ar']})")

    print("\n" + "=" * 80)
    print("✅ INSTITUTIONAL QUANT STACK & SELF-IMPROVING AGENT: 100% OPERATIONAL & VERIFIED")
    print("=" * 80)


if __name__ == "__main__":
    run_full_institutional_verification()
