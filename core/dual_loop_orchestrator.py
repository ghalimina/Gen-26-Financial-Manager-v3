#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/dual_loop_orchestrator.py — Dual-Loop Architecture Orchestrator
# Coordinates:
# 1. Fast Execution Loop (Intraday 10:00 - 14:30): Sub-second trade gating with
#    episodic memory veto checks and pre-compiled policy execution.
# 2. Slow Evolution Loop (Post-Market 15:00+): Forensic post-mortems on losing trades,
#    episodic memory consolidation, evolutionary factor mutation, and next-day policy compilation.
# =============================================================================

import os
import sys
import datetime
import logging
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.trade_post_mortem_engine import TradePostMortemEngine, PostMortemReport
from core.episodic_trade_memory import EpisodicTradeMemory
from core.alpha_factor_mutator import AlphaFactorMutator
from core.database_engine import db_engine

logger = logging.getLogger("GEN26.DualLoopOrchestrator")


class DualLoopOrchestrator:
    """
    Orchestrates the asynchronous dual-loop cognitive architecture for GEN-26.
    """

    # =========================================================================
    # FAST EXECUTION LOOP (INTRADAY)
    # =========================================================================

    @classmethod
    def fast_loop_screen_candidate(
        cls,
        ticker: str,
        current_features: Dict[str, Any],
        market_regime: str = "BULL_TREND"
    ) -> Dict[str, Any]:
        """
        Sub-second intraday screening guard:
        Queries episodic memory to ensure proposed trade does not replicate a past failure pattern.
        """
        return EpisodicTradeMemory.evaluate_trade_candidate(
            ticker=ticker,
            current_features=current_features,
            regime=market_regime
        )

    # =========================================================================
    # SLOW EVOLUTION LOOP (POST-MARKET CLOSE)
    # =========================================================================

    @classmethod
    def run_post_market_evolution_cycle(
        cls,
        closed_trades: Optional[List[Dict[str, Any]]] = None,
        market_regime: str = "BULL_TREND"
    ) -> Dict[str, Any]:
        """
        Executes post-market cognitive cycle:
        1. Forensic post-mortems on all losing trades from today's session.
        2. Persistence into SQLite episodic memory.
        3. Evolutionary alpha factor mutation and walk-forward verification.
        4. Next-day policy parameter compilation.
        """
        cycle_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info("Starting Post-Market Evolution Cycle at %s", cycle_time)

        # 1. Inspect closed trades
        sample_trades = closed_trades or [
            {
                "ticker": "COMI",
                "entry_price": 84.50,
                "exit_price": 81.20,
                "entry_features": {"volume_ratio": 0.65, "cmf": -0.12, "mfi": 62.0, "adx": 22.0, "spread_pct": 0.25},
                "exit_reason": "STOP_LOSS",
                "holding_period_days": 3,
                "slippage_pct": 0.20
            }
        ]

        post_mortem_reports = []
        for trade in sample_trades:
            pnl = ((trade["exit_price"] - trade["entry_price"]) / max(trade["entry_price"], 1e-4)) * 100.0
            if pnl < 0.0:  # Only diagnose losing trades
                report = TradePostMortemEngine.diagnose_trade(
                    ticker=trade["ticker"],
                    entry_price=trade["entry_price"],
                    exit_price=trade["exit_price"],
                    entry_features=trade.get("entry_features", {}),
                    exit_reason=trade.get("exit_reason", "STOP_LOSS"),
                    holding_period_days=trade.get("holding_period_days", 1),
                    slippage_pct=trade.get("slippage_pct", 0.15)
                )
                post_mortem_reports.append(report)
                # Persist into episodic memory
                EpisodicTradeMemory.record_post_mortem(report, regime=market_regime)

        # 2. Evolutionary Factor Mutation
        mutated_candidates = AlphaFactorMutator.evolve_generation(
            population_size=3,
            regime=market_regime
        )

        promoted_factors = [c for c in mutated_candidates if c.get("promoted", False)]

        # 3. Policy Compilation for tomorrow
        compiled_policy = {
            "compilation_timestamp": cycle_time,
            "target_regime": market_regime,
            "active_quarantined_count": len(post_mortem_reports),
            "promoted_factors_count": len(promoted_factors),
            "top_fitness_score": mutated_candidates[0]["fitness_score"] if mutated_candidates else 0.0,
            "ready_for_open": True
        }

        return {
            "timestamp": cycle_time,
            "cycle_status": "COMPLETED",
            "trades_diagnosed_count": len(post_mortem_reports),
            "post_mortems": [r.to_dict() for r in post_mortem_reports],
            "evolution_candidates": mutated_candidates,
            "promoted_factors": promoted_factors,
            "compiled_policy": compiled_policy,
            "summary_ar": (
                f"اكتملت دورة التطور الليلي: تم تشريح {len(post_mortem_reports)} صفقة خاسرة، "
                f"واختبار {len(mutated_candidates)} طفرة عوامل ألفا، مع ترقية {len(promoted_factors)} عامل للمصفوفة التشغيلية."
            )
        }
