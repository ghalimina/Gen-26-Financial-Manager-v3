#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/ensemble_decision_engine.py — Ensemble Consensus Decision Engine
# Unifies and synthesizes signals across all 6 Institutional Analytical Pillars:
# 1. Technical Multi-Horizon Rankings (MultiHorizonEngine)
# 2. Fundamental & DCF Fair Value (FundamentalDataEngine & CorporateActionsEngine)
# 3. Macroeconomic & CBE Corridor Regime (MacroEconomicEngine & RegimeHMMEngine)
# 4. London GDR & Global Commodities (GDRArbitrageEngine & AlternativeDataEngine)
# 5. Insiders & Institutional Smart Money Flows (InsiderTradingEngine & InstitutionalFlowEngine)
# 6. Arabic Financial NLP News Sentiment (NLPSentimentEngine)
#
# Consensus Voting Rule: Only issues "STRONG_BUY" if at least 4 out of 6 pillars agree (Score >= 78.0).
# Records decisions into SQLite Database & gen_decision_log.json.
# =============================================================================

import os
import sys
import json
import uuid
import datetime
import logging
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_price_service import MarketPriceService
from core.database_engine import SQLiteDatabaseEngine

logger = logging.getLogger("GEN26.EnsembleDecisionEngine")


class EnsembleDecisionEngine:
    """
    Final Master Quantitative Decision Engine synthesizing 6 Analytical Pillars.
    """

    PILLAR_WEIGHTS = {
        "technicals": 0.25,
        "fundamentals": 0.20,
        "macro": 0.15,
        "gdr_commodities": 0.15,
        "smart_money_insiders": 0.15,
        "nlp_sentiment": 0.10
    }

    @classmethod
    def evaluate_ensemble_consensus(
        cls,
        ticker: str,
        persist_decision: bool = True
    ) -> Dict[str, Any]:
        """
        Runs exhaustive consensus evaluation across all 6 analytical pillars for a stock.
        """
        sym_clean = ticker.upper().strip()
        if not sym_clean.endswith(".CA") and "." not in sym_clean:
            sym_clean = f"{sym_clean}.CA"

        canon = MarketPriceService.CANONICAL_PRICES.get(sym_clean, {})
        raw_price = canon.get("price") if isinstance(canon, dict) else None
        try:
            current_price = float(raw_price) if raw_price is not None else 10.0
        except (ValueError, TypeError):
            current_price = 10.0

        if current_price <= 0:
            current_price = 10.0

        pillars = {}
        pillar_votes = {"BULLISH": 0, "BEARISH": 0, "NEUTRAL": 0}

        # ---------------------------------------------------------------------
        # Pillar 1: Technical Multi-Horizon Rankings
        # ---------------------------------------------------------------------
        try:
            from core.multi_horizon_engine import MultiHorizonEngine
            tech_rank = MultiHorizonEngine.evaluate_stock_multi_horizon(sym_clean)
            tech_score = float(tech_rank.get("composite_rank_score", 60.0))
            if tech_score >= 68.0:
                tech_vote = "BULLISH"
            elif tech_score <= 40.0:
                tech_vote = "BEARISH"
            else:
                tech_vote = "NEUTRAL"
        except Exception:
            tech_score = 60.0
            tech_vote = "NEUTRAL"

        pillars["technicals"] = {
            "name_ar": "التحليل الفني متعدد الآفاق الزمنية (Technical Horizon)",
            "score": round(tech_score, 1),
            "vote": tech_vote,
            "weight": cls.PILLAR_WEIGHTS["technicals"]
        }
        pillar_votes[tech_vote] += 1

        # ---------------------------------------------------------------------
        # Pillar 2: Fundamental & DCF Intrinsic Fair Value
        # ---------------------------------------------------------------------
        try:
            from core.corporate_actions_engine import CorporateActionsEngine
            dcf = CorporateActionsEngine.calculate_fair_value(sym_clean)
            mos = float(dcf.get("margin_of_safety_pct", 10.0))
            if mos >= 12.0:
                fund_score = min(98.0, 70.0 + mos)
                fund_vote = "BULLISH"
            elif mos <= -10.0:
                fund_score = max(15.0, 50.0 + mos)
                fund_vote = "BEARISH"
            else:
                fund_score = 60.0
                fund_vote = "NEUTRAL"
        except Exception:
            fund_score = 60.0
            fund_vote = "NEUTRAL"

        pillars["fundamentals"] = {
            "name_ar": "التقييم الجوهري وهامش الأمان DCF (Intrinsic Valuation)",
            "score": round(fund_score, 1),
            "vote": fund_vote,
            "weight": cls.PILLAR_WEIGHTS["fundamentals"]
        }
        pillar_votes[fund_vote] += 1

        # ---------------------------------------------------------------------
        # Pillar 3: Macroeconomic & EGX Regime
        # ---------------------------------------------------------------------
        try:
            from core.regime_hmm_engine import RegimeHMMEngine
            reg_info = RegimeHMMEngine.detect_latent_regime()
            regime = reg_info.get("regime", "SIDEWAYS_CHOP")
            if regime == "STRONG_BULL":
                macro_score = 88.0
                macro_vote = "BULLISH"
            elif regime in ("BEAR_CORRECTION", "FLASH_CRASH"):
                macro_score = 30.0
                macro_vote = "BEARISH"
            else:
                macro_score = 58.0
                macro_vote = "NEUTRAL"
        except Exception:
            macro_score = 60.0
            macro_vote = "NEUTRAL"

        pillars["macro"] = {
            "name_ar": "بيئة الاقتصاد الكلي ونظام السوق HMM (Macro Regime)",
            "score": round(macro_score, 1),
            "vote": macro_vote,
            "weight": cls.PILLAR_WEIGHTS["macro"]
        }
        pillar_votes[macro_vote] += 1

        # ---------------------------------------------------------------------
        # Pillar 4: London GDR Arbitrage & Global Commodities
        # ---------------------------------------------------------------------
        try:
            from core.gdr_arbitrage_engine import GDRArbitrageEngine
            gdr = GDRArbitrageEngine.calculate_gdr_premium(sym_clean)
            spread = float(gdr.get("spread_pct", 0.0))
            if spread >= 1.5:
                gdr_score = 85.0
                gdr_vote = "BULLISH"
            elif spread <= -2.0:
                gdr_score = 35.0
                gdr_vote = "BEARISH"
            else:
                gdr_score = 55.0
                gdr_vote = "NEUTRAL"
        except Exception:
            gdr_score = 55.0
            gdr_vote = "NEUTRAL"

        pillars["gdr_commodities"] = {
            "name_ar": "مراجحة شهادات إيداع لندن والسلع (London GDR Arbitrage)",
            "score": round(gdr_score, 1),
            "vote": gdr_vote,
            "weight": cls.PILLAR_WEIGHTS["gdr_commodities"]
        }
        pillar_votes[gdr_vote] += 1

        # ---------------------------------------------------------------------
        # Pillar 5: Insiders & Smart Money Flows
        # ---------------------------------------------------------------------
        try:
            from core.institutional_flow_engine import InstitutionalFlowEngine
            flow = InstitutionalFlowEngine.evaluate_stock_flow(sym_clean)
            flow_score = float(flow.get("flow_score", 60.0))
            if flow_score >= 70.0:
                sm_vote = "BULLISH"
            elif flow_score <= 40.0:
                sm_vote = "BEARISH"
            else:
                sm_vote = "NEUTRAL"
        except Exception:
            flow_score = 60.0
            sm_vote = "NEUTRAL"

        pillars["smart_money_insiders"] = {
            "name_ar": "رادار تجميع المؤسسات والمطلعين (Smart Money Radar)",
            "score": round(flow_score, 1),
            "vote": sm_vote,
            "weight": cls.PILLAR_WEIGHTS["smart_money_insiders"]
        }
        pillar_votes[sm_vote] += 1

        # ---------------------------------------------------------------------
        # Pillar 6: Arabic Financial NLP News Sentiment
        # ---------------------------------------------------------------------
        try:
            from core.nlp_sentiment_engine import NLPSentimentEngine
            news_res = NLPSentimentEngine.analyze_stock_sentiment(sym_clean)
            sent_score = float(news_res.get("sentiment_score", 60.0))
            if sent_score >= 68.0:
                nlp_vote = "BULLISH"
            elif sent_score <= 40.0:
                nlp_vote = "BEARISH"
            else:
                nlp_vote = "NEUTRAL"
        except Exception:
            sent_score = 60.0
            nlp_vote = "NEUTRAL"

        pillars["nlp_sentiment"] = {
            "name_ar": "معالجة الأخبار والإفصاحات المالية NLP (Financial Sentiment)",
            "score": round(sent_score, 1),
            "vote": nlp_vote,
            "weight": cls.PILLAR_WEIGHTS["nlp_sentiment"]
        }
        pillar_votes[nlp_vote] += 1

        # ---------------------------------------------------------------------
        # Weighted Composite Score & Consensus Voting Aggregation
        # ---------------------------------------------------------------------
        composite_score = round(
            sum(p["score"] * p["weight"] for p in pillars.values()),
            1
        )

        bullish_count = pillar_votes["BULLISH"]
        bearish_count = pillar_votes["BEARISH"]

        # Strict Consensus Rule: 4+ out of 6 pillars must agree for STRONG_BUY
        if bullish_count >= 4 and composite_score >= 78.0:
            final_action = "STRONG_BUY"
            conviction = "VERY_HIGH"
            action_badge_ar = "🟢 شراء قوي بإجماع المحركات (Strong Buy)"
        elif bullish_count >= 3 and composite_score >= 65.0:
            final_action = "BUY"
            conviction = "HIGH"
            action_badge_ar = "🟢 شراء استثماري (Buy)"
        elif bearish_count >= 4 or composite_score < 35.0:
            final_action = "STRONG_SELL"
            conviction = "VERY_HIGH"
            action_badge_ar = "🔴 بيع قوي وتخارج فوري (Strong Sell)"
        elif bearish_count >= 3 or composite_score < 45.0:
            final_action = "SELL"
            conviction = "HIGH"
            action_badge_ar = "🔴 بيع وجني أرباح (Sell)"
        else:
            final_action = "HOLD"
            conviction = "MODERATE"
            action_badge_ar = "🟡 احتفاظ ومراقبة (Hold)"

        # Price Target & Stop Loss Levels
        target_1 = round(current_price * 1.08, 2)   # +8%
        target_2 = round(current_price * 1.18, 2)   # +18%
        stop_loss = round(current_price * 0.95, 2)  # -5%

        decision_id = f"ENS_{datetime.date.today().strftime('%Y%m%d')}_{sym_clean.replace('.', '_')}_{uuid.uuid4().hex[:4].upper()}"
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        decision_payload = {
            "decision_id": decision_id,
            "ticker": sym_clean,
            "current_price_egp": round(current_price, 2),
            "entry_price_egp": round(current_price, 2),
            "target_price_1_egp": target_1,
            "target_price_2_egp": target_2,
            "stop_loss_price_egp": stop_loss,
            "final_action": final_action,
            "conviction": conviction,
            "composite_score": composite_score,
            "bullish_pillar_count": bullish_count,
            "bearish_pillar_count": bearish_count,
            "total_pillars": 6,
            "consensus_ratio_pct": round((bullish_count / 6.0) * 100.0, 1),
            "action_badge_ar": action_badge_ar,
            "pillars_breakdown": pillars,
            "timestamp": now_str
        }

        # Persist to SQLite and JSON if requested
        if persist_decision:
            cls._save_decision_record(decision_payload)

        return decision_payload

    @classmethod
    def _save_decision_record(cls, payload: Dict[str, Any]) -> None:
        """Persists decision record into SQLite database and gen_decision_log.json."""
        # 1. SQLite Database persistence
        try:
            db = SQLiteDatabaseEngine()
            db.save_decision_record(
                decision_id=payload["decision_id"],
                ticker=payload["ticker"],
                action=payload["final_action"],
                entry_price=payload["entry_price_egp"],
                target_price=payload["target_price_1_egp"],
                stop_loss=payload["stop_loss_price_egp"],
                confidence_score=payload["composite_score"],
                status="ACTIVE"
            )
        except Exception as e:
            logger.debug(f"SQLite save_decision_record error: {e}")

        # 2. Disk JSON persistence
        log_file = os.path.join(WORKSPACE, "gen_decision_log.json")
        try:
            existing = []
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    existing = data if isinstance(data, list) else data.get("decisions", [])

            existing.append({
                "signal_id": payload["decision_id"],
                "date": datetime.date.today().isoformat(),
                "ticker": payload["ticker"],
                "action": payload["final_action"],
                "entry_price": payload["entry_price_egp"],
                "target_price": payload["target_price_1_egp"],
                "stop_loss": payload["stop_loss_price_egp"],
                "composite_score": payload["composite_score"],
                "status": "GENERATED",
                "timestamp": payload["timestamp"]
            })
            # Keep recent 200 decisions
            existing = existing[-200:]

            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug(f"JSON decision log error: {e}")

    @classmethod
    def scan_top_ensemble_opportunities(cls, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Scans top liquid EGX equities and ranks by ensemble consensus score.
        """
        from data.universe_manager import UniverseManager
        tickers = UniverseManager.get_all_tickers()[:30] # Top 30 for high-performance scan
        results = []

        for t in tickers:
            res = cls.evaluate_ensemble_consensus(t, persist_decision=False)
            results.append(res)

        results.sort(key=lambda x: x["composite_score"], reverse=True)
        return results[:limit]
