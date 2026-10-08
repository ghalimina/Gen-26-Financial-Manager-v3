#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/unified_pipeline_orchestrator.py — Unified Master System Pipeline Orchestrator
# End-to-End Operational Pipeline for Institutional Quantitative Operations:
# 1. Gathers multi-source intelligence (Mubasher, Al Borsa, Enterprise, CBE, GDRs/Commodities).
# 2. Computes 48-feature tensor and Two-Stage Meta-Labeling AI confidence.
# 3. Executes 7-Agent Quant Council deliberation and consensus voting.
# 4. Enforces 10 Books Quant rules & Mark Douglas psychology circuit breaker.
# 5. Validates dynamic trailing stops and sector concentration limits.
# 6. Persists complete audit records to SQLite (agent_council_votes).
# 7. Optionally triggers Autonomous Research Cycle for self-improvement.
# =============================================================================

import os
import sys
import json
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_price_service import MarketPriceService
from core.multi_source_intelligence import MultiSourceIntelligence
from core.deep_quant_fusion_engine import DeepQuantFusionEngine
from core.multi_agent_council import AgentCouncilOrchestrator
from core.quant_books_engine import QuantBooksEngine
from core.dynamic_risk_manager import DynamicRiskManager
from core.database_engine import db_engine
from core.autonomous_research_lab import AutonomousResearchLab
from core.notification_gateway import NotificationEngine
from core.theory_engine import TheoryEngine
from core.gdr_arbitrage_engine import GDRArbitrageEngine
from core.statistical_arbitrage_engine import StatisticalArbitrageEngine, EGX_KNOWN_PAIRS
from core.meta_labeling_engine import MetaLabelingEngine
from core.data_quality import DataQualityEngine
from core.trade_selection_model import TradeSelectionModel
from core.trade_post_mortem_engine import TradePostMortemEngine

logger = logging.getLogger("GEN26.UnifiedPipelineOrchestrator")


class UnifiedPipelineOrchestrator:
    """
    Unified Master Operational Pipeline Orchestrator for the GEN-26 Platform.
    """

    @classmethod
    def execute_unified_pipeline(
        cls,
        ticker: str,
        trigger_research: bool = False,
        portfolio_equity: float = 100_000.0
    ) -> Dict[str, Any]:
        """
        Executes end-to-end multi-agent, multi-source, and deep quant fusion pipeline for a stock.
        """
        sym = (ticker or "UNKNOWN.CA").upper().strip()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Fail-closed check for unknown / illiquid / invalid tickers
        if not sym or sym in ["UNKNOWN", "UNKNOWN.CA", "NONE", "NULL", "INVALID"] or "INVALID" in sym:
            return {
                "status": "FAILED_CLOSED",
                "ticker": sym or "UNKNOWN.CA",
                "timestamp": timestamp,
                "reason_ar": "الرمز المدخل غير صالح أو غير مقيد في البورصة المصرية (Fail-Closed).",
                "final_decision": "ABORT_AND_HOLD",
                "approved_for_execution": False,
                "multi_source_intelligence": None,
                "deep_quant_fusion": None,
                "council_deliberation": None,
                "risk_gates_passed": False
            }

        # Resolve live market price
        cp = MarketPriceService.get_latest_price(sym)
        if cp <= 0:
            cp = 100.0

        # --- Step 1: Gather Multi-Source Intelligence ---
        try:
            intel = MultiSourceIntelligence.get_all_intelligence(ticker=sym)
        except Exception as e:
            logger.warning("Multi-source intelligence fallback for %s: %s", sym, e)
            intel = {
                "status": "FALLBACK",
                "composite_sentiment_score": 0.50,
                "sentiment_label_ar": "محايد"
            }

        # --- Step 2: Deep Quant Feature Fusion & Two-Stage Meta-Labeling ---
        try:
            fusion = DeepQuantFusionEngine.compute_fusion(sym, current_price=cp)
        except Exception as e:
            logger.warning("Deep quant fusion fallback for %s: %s", sym, e)
            fusion = {
                "status": "FALLBACK",
                "primary_model": {"predicted_direction": "HOLD", "expected_return_pct": 0.0},
                "meta_confidence_model": {"probability_profitable": 0.50, "recommended_sizing_multiplier": 0.0}
            }

        # --- Step 3: 7-Agent Council Deliberation ---
        council = AgentCouncilOrchestrator.deliberate(sym, current_price=cp, portfolio_equity=portfolio_equity)

        # --- Step 4: 10 Books Quant Metrics & Psychology Circuit Breaker ---
        piotroski = QuantBooksEngine.calculate_piotroski_f_score(sym)
        lynch = QuantBooksEngine.evaluate_peter_lynch_metrics(sym)
        candlesticks = QuantBooksEngine.detect_candlestick_patterns(sym)
        murphy_adx = QuantBooksEngine.calculate_adx_trend_strength(sym)
        psych_status = QuantBooksEngine.get_psychology_guard_status()

        # --- Step 5: Dynamic Risk Invariants & Trailing Stop Calculation ---
        target_price = fusion.get("target_price", round(cp * 1.10, 2))
        stop_loss = fusion.get("stop_loss", round(cp * 0.95, 2))
        trailing_stop_res = DynamicRiskManager.compute_trailing_stop(
            entry_price=cp,
            peak_price=cp,
            current_price=cp,
            current_stop=stop_loss
        )

        # --- Step 5.5: Master Alpha Synthesizer & Golden Consensus Gate ---
        master_alpha = cls.synthesize_master_alpha(sym, current_price=cp, portfolio_equity=portfolio_equity)
        golden_gate = master_alpha.get("golden_consensus", {})
        is_golden = golden_gate.get("is_golden_consensus", False)

        # --- Step 6: Master Consensus Synthesis & Execution Approval ---
        council_verdict = council.get("consensus_verdict", "HOLD")
        primary_dir = fusion.get("primary_model", {}).get("predicted_direction", "RANGEBOUND")
        meta_prob = fusion.get("meta_confidence_model", {}).get("probability_profitable", 0.50)
        is_psych_locked = psych_status.get("is_locked", False)
        risk_approved = council.get("risk_sizer_vote", {}).get("approved", True)

        approved = (
            (is_golden or (council_verdict in ["STRONG_BUY", "BUY"] and primary_dir == "BULLISH")) and
            meta_prob >= 0.55 and
            not is_psych_locked and
            risk_approved and
            not master_alpha.get("cooling_off", {}).get("is_locked", False)
        )

        final_verdict = "APPROVED_BUY" if approved else "HOLD_OR_REJECT"
        if is_golden:
            final_verdict = "APPROVED_STRONG_BUY"

        # --- Step 7: Persist Deliberation to SQLite ---
        vote_dict = {
            "vote_id": council.get("vote_id", f"VOTE_{sym}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            "timestamp": timestamp,
            "ticker": sym,
            "market_analyst_vote": council.get("market_analyst_vote"),
            "fundamentalist_vote": council.get("fundamentalist_vote"),
            "technician_vote": council.get("technician_vote"),
            "quant_modeler_vote": council.get("quant_modeler_vote"),
            "risk_sizer_vote": council.get("risk_sizer_vote"),
            "consensus_verdict": "STRONG_BUY" if is_golden else council_verdict,
            "conviction_score": 95.0 if is_golden else council.get("conviction_score", 50.0)
        }
        try:
            db_engine.record_council_vote(vote_dict)
        except Exception as e:
            logger.warning("Failed to record council vote to SQLite: %s", e)

        # --- Step 8: Optional Autonomous Research Cycle ---
        research_res = None
        if trigger_research:
            try:
                research_res = AutonomousResearchLab.run_research_cycle(regime="BULL_TREND_HIGH_VOL")
            except Exception as e:
                logger.warning("Optional research cycle run failed: %s", e)

        # --- Step 9: Assemble Unified Master Report ---
        decision = {
            "status": "SUCCESS",
            "ticker": sym,
            "timestamp": timestamp,
            "current_price": cp,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "final_decision": final_verdict,
            "approved_for_execution": approved,
            "is_golden_consensus": is_golden,
            "golden_consensus_badge_ar": golden_gate.get("verdict_badge_ar", "⚪ استبعاد"),
            "composite_conviction_score": 95.0 if is_golden else round(
                (council.get("conviction_score", 70.0) * 0.5) + (meta_prob * 100.0 * 0.5), 1
            ),
            "master_alpha_synthesis": {
                "theories_passed_count": golden_gate.get("gates", {}).get("theories_passed_count", 0),
                "theories_gate_passed": golden_gate.get("gates", {}).get("theories_gate_passed", False),
                "dqs_score": golden_gate.get("gates", {}).get("dqs_score", 90.0),
                "expected_net_return_pct": golden_gate.get("gates", {}).get("expected_net_return_pct", 0.0),
                "gdr_spread_pct": golden_gate.get("gates", {}).get("gdr_spread_pct"),
                "cooling_off_locked": master_alpha.get("cooling_off", {}).get("is_locked", False),
                "rejection_reasons_ar": golden_gate.get("rejection_reasons_ar", [])
            },
            "multi_source_intelligence": {
                "composite_sentiment_score": intel.get("composite_sentiment_score", 0.5),
                "sentiment_label_ar": intel.get("sentiment_label_ar", "محايد"),
                "cbe_deposit_rate": intel.get("feed_4_cbe_telemetry", {}).get("cbe_deposit_rate_pct", 27.25),
                "headline_inflation": intel.get("feed_4_cbe_telemetry", {}).get("headline_cpi_inflation_pct", 26.50)
            },
            "deep_quant_fusion": {
                "feature_dimensions": fusion.get("features_tensor", {}).get("feature_dimensions", 48),
                "primary_direction": primary_dir,
                "meta_confidence_prob": meta_prob,
                "recommended_sizing_multiplier": fusion.get("meta_confidence_model", {}).get("recommended_sizing_multiplier", 0.0)
            },
            "theories_breakdown": master_alpha.get("theories_synthesis", {}).get("theories", {}),
            "council_deliberation": {
                "consensus_verdict": council_verdict,
                "conviction_score": council.get("conviction_score", 0.0),
                "bullish_votes": council.get("bullish_votes_count", 0),
                "bearish_votes": council.get("bearish_votes_count", 0)
            },
            "quant_books_summary": {
                "piotroski_f_score": piotroski.get("f_score", 7),
                "peter_lynch_category": lynch.get("category", "STALWART"),
                "candlestick_patterns_count": len(candlesticks),
                "murphy_adx_strength": murphy_adx.get("adx", 28.5),
                "psychology_guard_locked": is_psych_locked
            },
            "risk_and_execution_parameters": {
                "trailing_stop_stage": trailing_stop_res.get("trailing_stop_stage"),
                "ratcheted_stop_price": trailing_stop_res.get("calculated_stop_price"),
                "risk_reward_ratio": round((target_price - cp) / max(0.1, cp - stop_loss), 2),
                "sector_concentration_cap_pct": DynamicRiskManager.MAX_SECTOR_CONCENTRATION_PCT
            },
            "autonomous_research_cycle": research_res
        }

        return decision

    @classmethod
    def synthesize_master_alpha(
        cls,
        ticker: str,
        current_price: Optional[float] = None,
        portfolio_equity: float = 100_000.0
    ) -> Dict[str, Any]:
        """
        Master Alpha Synthesizer (Zenith Optimization Pillar 1):
        Nervous interconnection binding the 4 core institutional engines:
        1. TheoryEngine: 6 classical & institutional theories (Wyckoff, ICT, VCP, CAN SLIM, Dow, Elliott).
        2. GDRArbitrageEngine: London GDR parity spread & overnight gap forecast.
        3. StatisticalArbitrageEngine: Pairs co-integration Z-Score deviation.
        4. MetaLabelingEngine & DeepQuantFusion: 48-feature tensor, calibrated probability & expected net return.
        Enforces Golden Consensus Gate (STRONG_BUY iff all 5 criteria + anti-revenge cooling-off cleared).
        """
        sym = (ticker or "COMI.CA").upper().strip()
        cp = current_price or MarketPriceService.get_latest_price(sym)
        if cp <= 0:
            cp = 100.0

        # 1. Engine 1: 6 Theories Synthesis
        try:
            theories_res = TheoryEngine.evaluate_comprehensive_theories(sym, current_price=cp)
        except Exception as e:
            logger.warning("TheoryEngine evaluation error for %s: %s", sym, e)
            theories_res = {"theories": {}, "master_theory_score": 50.0}

        # 2. Engine 2: London GDR Lead-Lag Arbitrage
        try:
            has_gdr = sym in GDRArbitrageEngine.GDR_REGISTRY
            if has_gdr:
                gdr_res = GDRArbitrageEngine.calculate_gdr_premium(sym, override_cairo_price=cp)
                gdr_spread = float(gdr_res.get("spread_pct", 0.0))
            else:
                gdr_res = {"has_gdr": False, "spread_pct": 0.0, "status": "NO_GDR_LISTED"}
                gdr_spread = None
        except Exception as e:
            logger.warning("GDRArbitrageEngine error for %s: %s", sym, e)
            gdr_res = {"status": "NO_GDR", "spread_pct": 0.0}
            gdr_spread = None
            has_gdr = False

        # 3. Engine 3: Statistical Arbitrage & Pairs Z-Score
        stat_pair_info = None
        for pair in EGX_KNOWN_PAIRS:
            if pair["ticker_A"] == sym or pair["ticker_B"] == sym:
                try:
                    stat_pair_info = StatisticalArbitrageEngine.calculate_pair_spread_zscore(
                        pair["ticker_A"], pair["ticker_B"]
                    )
                    break
                except Exception as e:
                    logger.error(f"Error calculating pair spread Z-Score for {sym}: {e}")

        # 4. Engine 4: 48-factor Deep Quant Fusion & Calibrated Meta-Labeling
        try:
            fusion = DeepQuantFusionEngine.compute_fusion(sym, current_price=cp)
            p_calibrated = float(fusion.get("meta_confidence_model", {}).get("probability_profitable", 0.60))
        except Exception as e:
            logger.warning("DeepQuantFusion error for %s: %s", sym, e)
            fusion = {"features_tensor": {"feature_dimensions": 48}}
            p_calibrated = 0.60

        is_mega = sym in {
            "COMI.CA", "ESRS.CA", "TMGH.CA", "SWDY.CA", "ABUK.CA",
            "ETEL.CA", "MFPC.CA", "EKHO.CA", "FWRY.CA", "ORAS.CA"
        }
        fric_val = 1.10 if is_mega else 2.90
        exp_net_dict = MetaLabelingEngine.calculate_expected_net_return(
            p_calibrated_up=p_calibrated,
            target_pct=8.0,
            stop_loss_pct=3.5,
            ticker=sym,
            friction_pct=fric_val
        )
        e_net = float(exp_net_dict.get("expected_net_return_pct", 0.0))

        # 5. Data Quality Score
        dqs_dict = DataQualityEngine.get_stock_dqs(sym)
        dqs_score = float(dqs_dict.get("dqs", 90.0))

        # 6. EGX30 Market Trend Gate
        market_gate = TradeSelectionModel.evaluate_egx30_trend_gate()
        is_market_bull = market_gate.get("can_trade", True)

        # 7. Episodic Failure Memory: 48-Hour Cooling-Off Check
        is_cooling_off, rem_hours, cool_reason = TradePostMortemEngine.is_ticker_in_cooling_off(sym)

        # 8. Golden Consensus Filter
        consensus = TradeSelectionModel.evaluate_golden_consensus(
            ticker=sym,
            current_price=cp,
            theories_result=theories_res,
            dqs_score=dqs_score,
            gdr_spread_pct=gdr_spread if has_gdr else None,
            is_market_bull=is_market_bull,
            expected_net_return_pct=e_net,
            cooling_off_active=is_cooling_off
        )

        return {
            "ticker": sym,
            "current_price": cp,
            "golden_consensus": consensus,
            "theories_synthesis": theories_res,
            "gdr_arbitrage": gdr_res,
            "statistical_arbitrage": stat_pair_info,
            "deep_quant_fusion": fusion,
            "expected_net_return": exp_net_dict,
            "data_quality": dqs_dict,
            "market_regime_gate": market_gate,
            "cooling_off": {
                "is_locked": is_cooling_off,
                "remaining_hours": rem_hours,
                "reason_ar": cool_reason
            }
        }

