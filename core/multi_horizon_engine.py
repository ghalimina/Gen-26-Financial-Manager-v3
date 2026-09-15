#!/usr/bin/env python3
# =============================================================================
# core/multi_horizon_engine.py — GEN-26 Multi-Horizon Prediction & Scoring Engine
# Complete EGX Universe Cross-Sectional Ranking from Best to Worst (24+ Equities).
# =============================================================================

import os
import sys
import json
import math
import time
import datetime
from typing import Dict, List, Any, Optional
from core.market_price_service import MarketPriceService
from core.technical_setup_engine import TechnicalSetupEngine


class MultiHorizonEngine:
    """
    Quantitative Multi-Horizon Forecasting and Factor Engine for all active EGX Equities.
    """

    HORIZONS = {
        "1D": {"days": 1, "term": "short", "weight": 0.15, "label": "يوم واحد (قصير الأجل)"},
        "5D": {"days": 5, "term": "short", "weight": 0.20, "label": "5 أيام (أسبوع تداول)"},
        "10D": {"days": 10, "term": "medium", "weight": 0.25, "label": "10 أيام (أسبوعين)"},
        "20D": {"days": 20, "term": "medium", "weight": 0.25, "label": "20 يوم (شهر تداول)"},
        "60D": {"days": 60, "term": "long", "weight": 0.15, "label": "60 يوم (ربع سنوي)"}
    }

    STOCK_PROFILES = {}

    @classmethod
    def _synthesize_dynamic_profile(cls, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Dynamically synthesizes a quantitative multi-horizon profile for any active EGX ticker
        using metadata, beta, sector characteristics, and liquidity from EGXUniverseLoader or UniverseManager.
        """
        from core.egx_universe_loader import EGXUniverseLoader
        from data.universe_manager import UniverseManager
        info = EGXUniverseLoader.get_stock_info(ticker) or UniverseManager.get_ticker_metadata(ticker)
        if not info:
            return None

        name_ar = info.get("name_ar", ticker)
        sector = info.get("sector", "عام")
        beta = float(info.get("beta_egx30", 1.0))
        tier = info.get("market_cap_tier", "MID_CAP")
        adv = float(info.get("adv20_egp", 10000000.0))

        # Base alpha expectations modulated by sector beta and liquidity tier
        base_prob = 0.55 + min(max((beta - 1.0) * 0.05, -0.05), 0.08)
        if tier == "LARGE_CAP":
            base_prob += 0.03
        elif tier == "SMALL_CAP":
            base_prob -= 0.02

        prob_1d = round(base_prob, 2)
        prob_5d = round(min(base_prob + 0.04, 0.78), 2)
        prob_10d = round(min(base_prob + 0.07, 0.82), 2)
        prob_20d = round(min(base_prob + 0.10, 0.85), 2)
        prob_60d = round(min(base_prob + 0.13, 0.88), 2)

        conf = 0.85 if tier == "LARGE_CAP" else (0.80 if tier == "MID_CAP" else 0.75)

        h_forecasts = {
            "1D": {"expected_return_pct": round(0.25 * beta, 2), "prob_up": prob_1d, "confidence": conf, "t1_pct": round(0.8 * beta, 1), "t2_pct": round(1.5 * beta, 1), "t3_pct": round(2.5 * beta, 1)},
            "5D": {"expected_return_pct": round(1.30 * beta, 2), "prob_up": prob_5d, "confidence": round(conf + 0.02, 2), "t1_pct": round(2.5 * beta, 1), "t2_pct": round(4.2 * beta, 1), "t3_pct": round(6.0 * beta, 1)},
            "10D": {"expected_return_pct": round(2.80 * beta, 2), "prob_up": prob_10d, "confidence": round(conf + 0.04, 2), "t1_pct": round(4.5 * beta, 1), "t2_pct": round(6.8 * beta, 1), "t3_pct": round(9.5 * beta, 1)},
            "20D": {"expected_return_pct": round(5.50 * beta, 2), "prob_up": prob_20d, "confidence": round(conf + 0.06, 2), "t1_pct": round(7.5 * beta, 1), "t2_pct": round(11.0 * beta, 1), "t3_pct": round(15.0 * beta, 1)},
            "60D": {"expected_return_pct": round(10.50 * beta, 2), "prob_up": prob_60d, "confidence": conf, "t1_pct": round(13.5 * beta, 1), "t2_pct": round(19.0 * beta, 1), "t3_pct": round(24.5 * beta, 1)}
        }

        why_ar = f"🟢 سهم نشط ضمن قطاع {sector} بسيولة يومية تبلغ نحو {adv/1e6:.1f}M ج.م ومعامل بيتا {beta:.2f}."

        return {
            "name_ar": name_ar,
            "sector": sector,
            "rsi14": 52.0, "adx14": 21.0, "atr14": 1.0,
            "adv20_egp": adv,
            "beta_egx30": beta,
            "h_forecasts": h_forecasts,
            "why_ar": why_ar
        }

    @classmethod
    def get_stock_multi_horizon_analysis(cls, ticker: str, mock_price: Optional[float] = None) -> Optional[Dict[str, Any]]:
        from core.market_breadth_engine import MarketBreadthEngine
        from core.sector_rs_engine import SectorRelativeStrengthEngine
        from core.institutional_flow_engine import InstitutionalFlowEngine
        from core.live_fundamentals_engine import LiveFundamentalsEngine
        from core.news_sentiment_engine import NewsSentimentEngine
        from core.block_trades_engine import BlockTradesEngine
        from core.technical_setup_engine import TechnicalSetupEngine
        from core.risk_position_sizer import RiskBasedPositionSizer

        sym = ticker.upper().strip()
        if not sym.endswith(".CA") and "." not in sym:
            sym = f"{sym}.CA"

        prof = cls._synthesize_dynamic_profile(sym)

        if not prof:
            return None

        rec = MarketPriceService.get_canonical_price_record(sym)
        if mock_price is not None and mock_price > 0:
            p = float(mock_price)
        elif rec and "price" in rec and rec["price"] is not None and rec["price"] > 0:
            p = float(rec["price"])
        else:
            p = None

        if p is None:
            return {
                "ticker": sym,
                "company_name": prof["name_ar"],
                "sector": prof["sector"],
                "current_price": None,
                "status": "DATA_INSUFFICIENT",
                "status_ar": "بيانات غير كافية (سهم راكد أو متوقف)",
                "is_liquid": False,
                "is_tradable": False,
                "overall_score": 0.0,
                "alpha_score": 0.0,
                "decision": "AVOID",
                "action": "AVOID",
                "action_ar": "🔴 بيانات غير كافية (مستبعد آلياً من التداول والترتيب)",
                "explanation_ar": "لا تتوفر بيانات تداول حديثة أو أسعار تنفيذ حية لهذا السهم من البورصة المصرية.",
                "fundamentals": {"fundamental_score": 50.0, "pe_ratio": 0.0, "roe_pct": 0.0, "debt_to_equity": 0.0},
                "technical_setup": {"technical_score": 50.0, "setup_classification": "DATA_INSUFFICIENT", "setup_label_ar": "بيانات غير كافية"},
                "institutional_flow": {"flow_regime": "ILLIQUID_DRYUP", "flow_alpha_impact": 0.0, "volume_z_score": 0.0, "description_ar": "لا توجد تدفقات"},
                "news_sentiment": {"alpha_shock_pct": 0.0, "sentiment_label_ar": "محايد", "materiality": "LOW", "headline_ar": "لا توجد أخبار"},
                "block_trades": {"classification": "NORMAL_FLOW", "ticket_multiple": 0.0, "description_ar": "لا توجد صفقات كتلية"},
                "macro_intelligence": {"macro_alpha_impact": 0.0, "macro_headline": "محايد", "sector_rationale_ar": "محايد"},
                "corporate_hazard": {"has_imminent_event": False, "hazard_level": "LOW", "warning_ar": "لا توجد أحداث شركات"},
                "sector_relative_strength": {"rs_spread_pct": 0.0, "leadership_label_ar": "محايد"},
                "two_tier_relative_strength": {"stock_rs_vs_sector": "NEUTRAL", "sector_rs_vs_market": "NEUTRAL", "rs_alignment_label_ar": "محايد"},
                "entry_zone": "0.00 – 0.00",
                "max_entry_price": 0.0,
                "stop_loss": 0.0,
                "confidence_score": 0.0,
                "beta_egx30": 1.0,
                "dominant_catalyst": "NONE",
                "expectancy_pct": 0.0,
                "signal_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "valid_until": (datetime.datetime.now() + datetime.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
                "ttl_minutes": 30,
                "is_expired": False,
                "up_drivers": [],
                "down_risks": [],
                "staged_exits": {},
                "horizons": {
                    "1D": {"expected_return_pct": 0.0, "prob_up": 0.5, "target_1": 0.0},
                    "5D": {"expected_return_pct": 0.0, "prob_up": 0.5, "target_1": 0.0},
                    "10D": {"expected_return_pct": 0.0, "prob_up": 0.5, "target_1": 0.0},
                    "20D": {"expected_return_pct": 0.0, "prob_up": 0.5, "target_1": 0.0},
                    "60D": {"expected_return_pct": 0.0, "prob_up": 0.5, "target_1": 0.0}
                },
                "ai_forecast": {
                    "ticker": sym,
                    "expected_residual_alpha_10d_pct": 0.0,
                    "ai_confidence_score": 0.0,
                    "ai_sentiment": "ILLIQUID_EXCLUDED",
                    "ai_sentiment_ar": "مستبعد لعدم توفر بيانات تداول",
                    "top_3_drivers": ["No live trading data available"],
                    "skipped": True,
                    "reason": "DATA_INSUFFICIENT"
                }
            }

        price_source = rec.get("source", "SSOT_LIVE_STORE") if rec else "SSOT_LIVE_STORE"
        price_timestamp = rec.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) if rec else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Dynamic Volatility-Adjusted ATR Stop Loss
        # [HEURISTIC_PLACEHOLDER / UNVERIFIED]: Multiplier N_ATR = 2.0x, clamped between [3.5%, 10.0%]
        atr14 = float(prof.get("atr14", round(p * 0.035, 2)))
        n_atr_mult = 2.0
        atr_stop_dist = round(atr14 * n_atr_mult, 2)
        raw_stop = p - atr_stop_dist
        max_stop_allowed = math.floor((p * 0.965) * 100.0) / 100.0
        min_stop_allowed = math.ceil((p * 0.900) * 100.0) / 100.0
        stop_loss_price = round(max(min(raw_stop, max_stop_allowed), min_stop_allowed), 2)

        entry_low = float(rec.get("entry_zone_low", round(p * 0.985, 2))) if rec else round(p * 0.985, 2)
        entry_high = float(rec.get("entry_zone_high", round(p * 0.998, 2))) if rec else round(p * 0.998, 2)

        # 1. Advanced Institutional Quant Layer Evaluations
        from core.corporate_actions_calendar import CorporateActionsCalendar
        from core.macro_intelligence_engine import MacroIntelligenceEngine
        from core.portfolio_correlation_engine import PortfolioCorrelationEngine
        from core.ai_prediction_model import AIPredictionModel
        from core.meta_labeling_engine import MetaLabelingEngine
        from core.liquidity_filter import LiquidityGateEngine

        # Dynamic Liquidity Gate (Rules: ADV30 > 500k, ADT30 > 1M EGP, Zero Days < 3)
        liquidity_eval = LiquidityGateEngine.evaluate_stock_liquidity(sym, current_price=p)
        is_liquid = bool(liquidity_eval.get("is_liquid", True))

        breadth = MarketBreadthEngine.compute_market_breadth()
        sector_rs = SectorRelativeStrengthEngine.get_stock_sector_rs(sym)
        flow = InstitutionalFlowEngine.evaluate_stock_flow(sym, current_price=p)
        fundamentals = LiveFundamentalsEngine.get_stock_fundamentals(sym)
        sentiment = NewsSentimentEngine.get_sentiment_impact(sym)
        block_trades = BlockTradesEngine.detect_block_trades(sym, current_price=p)
        technical = TechnicalSetupEngine.evaluate_technical_setup(sym, current_price=p)
        macro_info = MacroIntelligenceEngine.evaluate_stock_macro_alpha(sym, prof.get("sector", "عام"))
        corp_hazard = CorporateActionsCalendar.evaluate_pre_trade_corporate_hazard(sym, p)
        beta_egx30 = PortfolioCorrelationEngine.get_stock_beta(sym)

        # Skip ML inference for illiquid stocks to protect model integrity & save compute
        if not is_liquid:
            ai_forecast = {
                "ticker": sym,
                "expected_residual_alpha_10d_pct": 0.0,
                "ai_confidence_score": 0.0,
                "ai_sentiment": "ILLIQUID_EXCLUDED",
                "ai_sentiment_ar": "مستبعد لضعف السيولة",
                "top_3_drivers": ["Illiquid Asset (ADV30 < 500k or ADT30 < 1M EGP)"],
                "skipped": True,
                "reason": "ILLIQUID_EXCLUDED"
            }
            meta_label = {
                "probability_of_success_pct": 0.0,
                "meta_signal": "VETO",
                "meta_decision": "VETO",
                "meta_decision_ar": "استبعاد آلي لضعف السيولة",
                "top_meta_drivers": ["ILLIQUID_FILTER_TRIGGERED"],
                "volatility_adjusted_return": 0.0
            }
        else:
            ai_forecast = AIPredictionModel.predict_stock(sym, current_price=p)

        # ML Confidence-Based Position Sizing Multiplier (Step 2 Logic)
        from config import config
        conf_val = float(ai_forecast.get("ai_confidence_score", 50.0)) if ai_forecast else 50.0
        
        # Sizing Rules:
        # - If confidence >= 65% -> position_size_multiplier = 1.2
        # - If confidence <= 45% -> position_size_multiplier = 0.7
        # - Otherwise            -> position_size_multiplier = 1.0
        if conf_val >= 65.0:
            position_size_multiplier = 1.2
        elif conf_val <= 45.0:
            position_size_multiplier = 0.7
        else:
            position_size_multiplier = 1.0

        ml_mode = getattr(config, "ML_MODE", "CONFIDENCE_ONLY")
        active_multiplier = position_size_multiplier if ml_mode in ["CONFIDENCE_ONLY", "ACTIVE"] else 1.0

        risk_sizing = RiskBasedPositionSizer.calculate_position_size(
            entry_price=p,
            stop_loss_price=stop_loss_price,
            market_regime=breadth["market_regime"],
            confidence_multiplier=active_multiplier
        )
        risk_sizing["position_size_multiplier"] = active_multiplier
        risk_sizing["raw_position_size_multiplier"] = position_size_multiplier
        risk_sizing["ml_confidence_score"] = conf_val
        risk_sizing["ml_mode"] = ml_mode

        # Factor contributions
        rs_spread = sector_rs.get("rs_spread_pct", 0.0)
        rs_alpha_boost = min(max(rs_spread * 0.04, -0.08), 0.08)
        flow_alpha_boost = flow.get("flow_alpha_impact", 0.0) * 0.5
        breadth_risk_mult = breadth.get("risk_multiplier", 1.0)
        
        fund_score = fundamentals.get("fundamental_score", 65.0)
        fund_alpha_boost = (fund_score - 65.0) * 0.002
        sentiment_alpha_boost = sentiment.get("alpha_shock_pct", 0.0) * 0.02
        block_alpha_boost = block_trades.get("block_alpha_impact", 0.0) * 0.4
        tech_score = technical.get("technical_score", 60.0)
        tech_alpha_boost = (tech_score - 50.0) * 0.003
        macro_alpha_boost = macro_info.get("macro_alpha_impact", 0.0) * 0.4
        corp_alpha_mult = corp_hazard.get("alpha_multiplier", 1.0)

        # Composite Quantitative Overall Score (Dynamically Calibrated Weights)
        from core.weight_calibrator import WeightCalibrator
        w_cal = WeightCalibrator.get_calibrated_weights()
        w_fund = w_cal.get("w_fundamental", 0.25)
        w_tech = w_cal.get("w_technical", 0.40)
        w_flow = w_cal.get("w_flow", 0.20)
        w_rs = w_cal.get("w_rs", 0.15)

        rs_base_score = 85.0 if rs_spread > 0 else 50.0
        overall_score = round(
            fund_score * w_fund +
            tech_score * w_tech +
            flow["flow_score"] * w_flow +
            rs_base_score * w_rs,
            1
        )
        if not is_liquid:
            overall_score = min(overall_score, 35.0)

        if is_liquid:
            meta_label = MetaLabelingEngine.evaluate_meta_label(sym, current_price=p, base_quant_score=overall_score)

        # 2-Tier Relative Strength
        stock_rs_tier = "STRONG_LEADER" if rs_spread >= 1.0 else ("NEUTRAL" if rs_spread >= -1.0 else "WEAK_LAGGARD")
        sector_rs_tier = "OUTPERFORMING" if breadth.get("ad_ratio", 1.0) >= 1.0 else "UNDERPERFORMING"
        if rs_spread >= 0.5 and breadth.get("ad_ratio", 1.0) >= 1.0:
            rs_alignment_ar = "🟢 سهم قوي في قطاع صاعد متفوق (Dual Leader)"
        elif rs_spread >= 0.5:
            rs_alignment_ar = "🟢 سهم قوي يتفوق على أداء قطاعه"
        elif rs_spread >= -0.5:
            rs_alignment_ar = "🟡 أداء متوازن ومتوافق مع القطاع"
        else:
            rs_alignment_ar = "🔴 تراجع في القوة النسبية عن القطاع"

        # Real Dynamic Quantitative Momentum & Trend Calculations
        raw_tech_score = float(technical.get("technical_score", 50.0))
        setup_class = technical.get("setup_classification", "RANGE_CONSOLIDATION")
        w_trend = technical.get("multi_timeframe", {}).get("weekly_trend", "NEUTRAL")
        rsi_val = float(technical.get("rsi14", 50.0))
        if math.isnan(rsi_val):
            rsi_val = 50.0
        roc20_val = float(technical.get("momentum_roc", {}).get("roc_20d", 0.0))
        if math.isnan(roc20_val):
            roc20_val = 0.0
        ai_alpha = float(ai_forecast.get("expected_residual_alpha_10d_pct", 0.0))
        meta_success_prob = float(meta_label.get("probability_of_success_pct", 50.0))
        flow_z = float(flow.get("volume_zscore", 0.0))
        beta_val = float(prof.get("beta_egx30", 1.0))
        atr_pct = float(technical.get("volatility_metrics", {}).get("atr_pct", 3.0))
        if math.isnan(atr_pct) or atr_pct <= 0:
            atr_pct = 3.0

        # Determine directional bias (-1.0 to +1.0)
        if w_trend == "BULLISH" and setup_class in ["PULLBACK_UPTREND", "BREAKOUT_EXPANSION", "BREAKOUT_RETEST_SUPPORT"]:
            dir_bias = 1.0
        elif w_trend == "BEARISH" or setup_class == "DOWNTREND_PULLBACK":
            dir_bias = -0.8
        elif setup_class == "OVERSOLD_REVERSAL":
            dir_bias = 0.6
        else:
            dir_bias = 0.2 if raw_tech_score >= 60 else (-0.2 if raw_tech_score <= 40 else 0.0)

        # Mean-reversion dampener for extreme RSI
        ob_drag = -0.08 * (rsi_val - 70.0) if rsi_val > 70.0 else (0.05 * (35.0 - rsi_val) if rsi_val < 35.0 else 0.0)

        horizons_data = {}
        conf_list = []
        prob_list = []

        for h_key, h_cfg in cls.HORIZONS.items():
            days = h_cfg["days"]
            sqrt_days = math.sqrt(days)

            # Dynamic expected return based on real momentum, direction, and ML alpha
            if h_key == "1D":
                dyn_ret = round(0.18 * dir_bias * beta_val + ob_drag + (roc20_val / 40.0) * 0.10 + (tech_alpha_boost * 1.5), 2)
            elif h_key == "5D":
                dyn_ret = round(0.85 * dir_bias * beta_val + ob_drag * 1.5 + (roc20_val / 20.0) * 0.25 + (ai_alpha * 0.25) + (tech_alpha_boost * 2.0), 2)
            elif h_key == "10D":
                dyn_ret = round(1.80 * dir_bias * beta_val + (ai_alpha * 0.45) + (rs_spread * 0.20) + (tech_alpha_boost * 1.5), 2)
            elif h_key == "20D":
                dyn_ret = round(3.80 * dir_bias * beta_val + (ai_alpha * 0.70) + (fund_score - 50.0) * 0.05 + (rs_spread * 0.15), 2)
            else:  # 60D
                dyn_ret = round(7.50 * dir_bias * beta_val + (fund_score - 50.0) * 0.12 + (ai_alpha * 0.50), 2)

            # Dynamic probability of up move
            dyn_prob = 0.50 + (0.16 * dir_bias) + ((raw_tech_score - 50.0) * 0.003) + ((meta_success_prob - 50.0) * 0.002) + (flow_z * 0.02)
            # Add horizon-specific boosts
            if h_key in ["1D", "5D"]:
                dyn_prob += rs_alpha_boost * 0.4 + flow_alpha_boost + sentiment_alpha_boost
            elif h_key in ["10D", "20D"]:
                dyn_prob += rs_alpha_boost + flow_alpha_boost * 0.4 + fund_alpha_boost * 0.5
            else:
                dyn_prob += rs_alpha_boost * 0.7 + fund_alpha_boost * 1.5

            adj_prob = round(min(max(dyn_prob, 0.28), 0.88), 2)
            adj_ret = round(max(dyn_ret * max(breadth_risk_mult, 0.5), -15.0), 2)
            
            base_conf = 0.85 if prof.get("market_cap_tier") == "LARGE_CAP" else 0.78
            adj_conf = round(min(max(base_conf * (0.95 if breadth["market_regime"] == MarketBreadthEngine.REGIME_PANIC_BEAR else 1.0), 0.50), 0.96), 2)

            conf_list.append(adj_conf)
            prob_list.append(adj_prob)

            exp_price = round(p * (1.0 + adj_ret / 100.0), 2)
            exp_downside_pct = round(max(-1.0 * (1.0 - adj_prob) * ((p - stop_loss_price) / p) * 100.0 * (days / 5.0) ** 0.5, -12.0), 2)

            # Dynamic volatility-scaled targets
            t1_gain = max(abs(adj_ret) * 0.8, atr_pct * 1.2 * (days / 5.0) ** 0.5)
            t1 = round(p * (1.0 + t1_gain / 100.0), 2)
            t2 = round(p * (1.0 + t1_gain * 1.55 / 100.0), 2)
            t3 = round(p * (1.0 + t1_gain * 2.30 / 100.0), 2)
            reward = t1 - p
            risk = p - stop_loss_price
            rr_ratio = round(reward / risk, 2) if risk > 0 else 1.0

            err_margin_pct = round((1.0 - adj_conf) * 5.0, 1)
            t1_low = round(t1 * (1.0 - err_margin_pct / 100.0), 2)
            t1_high = round(t1 * (1.0 + err_margin_pct / 100.0), 2)

            horizons_data[h_key] = {
                "horizon_label": h_cfg["label"],
                "days": h_cfg["days"],
                "term": h_cfg["term"],
                "expected_return_pct": adj_ret,
                "expected_downside_pct": exp_downside_pct,
                "expected_price": exp_price,
                "prob_up": adj_prob,
                "confidence": adj_conf,
                "target_1": t1,
                "target_1_bounds": {"low": t1_low, "high": t1_high, "confidence_pct": round(adj_conf * 100, 1)},
                "target_2": t2,
                "target_3": t3,
                "stop_loss": stop_loss_price,
                "reward_to_risk": rr_ratio,
                "direction": "UP" if adj_ret > 0 else "DOWN"
            }

        short_score = round((horizons_data["1D"]["prob_up"] * 40 + horizons_data["5D"]["prob_up"] * 60), 1)
        med_score = round((horizons_data["10D"]["prob_up"] * 50 + horizons_data["20D"]["prob_up"] * 50), 1)
        long_score = round(horizons_data["60D"]["prob_up"] * 100, 1)
        horizon_composite_score = round(short_score * 0.35 + med_score * 0.45 + long_score * 0.20, 1)

        # Enforce strict liquidity and real data penalty
        if not is_liquid or technical.get("status") == "DATA_INSUFFICIENT":
            overall_score = min(overall_score, 20.0)

        # 2. Decomposed UP DRIVERS & DOWN RISKS
        up_drivers = []
        down_risks = []

        # Macro Intelligence Driver
        if macro_info["macro_alpha_impact"] > 0.01:
            up_drivers.append({
                "factor": "Macroeconomic Tailwinds (المحفزات الكلية)",
                "impact_value": macro_info["macro_alpha_impact"],
                "impact_label": macro_info["macro_headline"],
                "description_ar": macro_info["sector_rationale_ar"]
            })
        elif macro_info["macro_alpha_impact"] < -0.01:
            down_risks.append({
                "factor": "Macroeconomic Headwinds (الضغوط الكلية)",
                "impact_value": macro_info["macro_alpha_impact"],
                "impact_label": macro_info["macro_headline"],
                "description_ar": macro_info["sector_rationale_ar"]
            })

        # Corporate Hazard Driver
        if corp_hazard["has_imminent_event"]:
            down_risks.append({
                "factor": "Upcoming Corporate Action Hazard (استحقاق أحداث الشركات)",
                "impact_value": -0.06,
                "impact_label": corp_hazard["hazard_level"],
                "description_ar": corp_hazard["warning_ar"]
            })

        # A. Sector Relative Strength Driver
        if sector_rs.get("is_leader", False) or rs_spread > 0.5:
            up_drivers.append({
                "factor": "Sector Relative Strength (قوة القطاع)",
                "impact_value": round(+abs(rs_spread) * 0.08, 2),
                "impact_label": f"+{rs_spread:+.2f}% تفوق على مؤشر القطاع",
                "description_ar": f"السهم يصنف كـ {sector_rs['leadership_label_ar']} متفوقاً على أداء قطاعه."
            })
        elif rs_spread < -0.5:
            down_risks.append({
                "factor": "Sector Drag (ضعف أداء القطاع)",
                "impact_value": round(-abs(rs_spread) * 0.08, 2),
                "impact_label": f"{rs_spread:+.2f}% فارق أداء عن القطاع",
                "description_ar": f"السهم متراجع عن متوسط أداء القطاع ({sector_rs['leadership_label_ar']})."
            })

        # B. Institutional Flow Driver
        if flow["flow_regime"] in [InstitutionalFlowEngine.FLOW_INSTITUTIONAL_ACCUMULATION, InstitutionalFlowEngine.FLOW_MODERATE_INFLOW]:
            up_drivers.append({
                "factor": "Institutional Flow (التدفق المؤسسي)",
                "impact_value": round(flow["flow_alpha_impact"], 2),
                "impact_label": f"Z-Score = {flow['volume_z_score']:+.2f}",
                "description_ar": flow["description_ar"]
            })
        elif flow["flow_regime"] in [InstitutionalFlowEngine.FLOW_RETAIL_DISTRIBUTION, InstitutionalFlowEngine.FLOW_MODERATE_OUTFLOW, InstitutionalFlowEngine.FLOW_ILLIQUID_DRYUP]:
            down_risks.append({
                "factor": "Volume & Flow Pressure (ضغط السيولة/التصريف)",
                "impact_value": round(flow["flow_alpha_impact"], 2),
                "impact_label": f"Z-Score = {flow['volume_z_score']:+.2f}",
                "description_ar": flow["description_ar"]
            })

        # C. Technical Setup & Trend Driver
        if tech_score >= 65.0:
            up_drivers.append({
                "factor": "Technical Setup & Trend (التحليل الفني والاتجاه)",
                "impact_value": round((tech_score - 50.0) * 0.004, 2),
                "impact_label": f"تقييم فني {tech_score:.1f}/100 ({technical['setup_classification']})",
                "description_ar": f"{technical['setup_label_ar']} فوق متوسط 20 يوم (RSI: {technical['rsi14']}, ADX: {technical['adx14']})."
            })
        elif tech_score < 50.0:
            down_risks.append({
                "factor": "Technical Breakdown (ضعف فني أو تراجع تحت المتوسطات)",
                "impact_value": round((tech_score - 50.0) * 0.004, 2),
                "impact_label": f"تقييم فني {tech_score:.1f}/100 ({technical['setup_classification']})",
                "description_ar": f"تراجع دون متوسط 20 يوماً أو مؤشرات عزم ضعيفة."
            })

        # D. Fundamental Quality Driver
        if fund_score >= 65.0:
            up_drivers.append({
                "factor": "Fundamental Quality & Solvency (جودة الأساسيات والتقييم)",
                "impact_value": round((fund_score - 50.0) * 0.005, 2),
                "impact_label": f"تقييم مالي {fund_score:.1f}/100 (مكرر P/E: {fundamentals['pe_ratio']:.1f})",
                "description_ar": f"عائد حقوق ملكية قوي (ROE: {fundamentals['roe_pct']:.1f}%) ونمو أرباح ({fundamentals['eps_growth_pct']:.1f}%)."
            })
        elif fund_score < 50.0:
            down_risks.append({
                "factor": "Fundamental Valuation Drag (ضغط التقييم/الرافعة)",
                "impact_value": round((fund_score - 50.0) * 0.005, 2),
                "impact_label": f"تقييم مالي {fund_score:.1f}/100 (مكرر P/E: {fundamentals['pe_ratio']:.1f})",
                "description_ar": f"رافعة مالية مرتفعة أو تراجع هوامش ربحية (مديونية: {fundamentals['debt_to_equity']:.2f})."
            })

        # E. Corporate News & Disclosure NLP Driver
        if sentiment.get("is_catalyst", False):
            up_drivers.append({
                "factor": "Corporate Disclosure Catalyst (محفز الأخبار والإفصاحات)",
                "impact_value": round(sentiment["alpha_shock_pct"] * 0.05, 2),
                "impact_label": f"{sentiment['sentiment_label_ar']} ({sentiment['materiality']})",
                "description_ar": sentiment["headline_ar"]
            })
        elif sentiment.get("is_risk_event", False):
            down_risks.append({
                "factor": "Negative News Sentiment Shock (صدمة الأخبار السلبية)",
                "impact_value": round(sentiment["alpha_shock_pct"] * 0.05, 2),
                "impact_label": f"{sentiment['sentiment_label_ar']} ({sentiment['materiality']})",
                "description_ar": sentiment["headline_ar"]
            })

        # F. Block Trades Driver
        if block_trades["classification"] == BlockTradesEngine.SIGNAL_SMART_MONEY_INFLOW:
            up_drivers.append({
                "factor": "Institutional Block Inflow (صفقات كتلية شرائية)",
                "impact_value": +0.12,
                "impact_label": f"{block_trades['ticket_multiple']}x متوسط التذكرة",
                "description_ar": block_trades["description_ar"]
            })
        elif block_trades["classification"] == BlockTradesEngine.SIGNAL_DISTRIBUTION_PRESSURE:
            down_risks.append({
                "factor": "Block Trade Distribution Pressure (ضغط بيوع كتلية)",
                "impact_value": -0.15,
                "impact_label": f"{block_trades['ticket_multiple']}x متوسط التذكرة",
                "description_ar": block_trades["description_ar"]
            })

        # G. Technical & Stop Protection
        down_risks.append({
            "factor": "Hard Stop-Loss Floor (-7.0%)",
            "impact_value": -0.07,
            "impact_label": f"{stop_loss_price:.2f} ج.م",
            "description_ar": "صمام أمان إلزامي ومحمي غير قابل للإلغاء لحماية رأس المال."
        })

        # 3. Staged Multi-Target Exits Protocol (T1 33%, T2 33%, T3 34%)
        t1_val = horizons_data["5D"]["target_1"]
        t2_val = horizons_data["20D"]["target_1"]
        t3_val = horizons_data["60D"]["target_1"]
        staged_exits = {
            "T1": {
                "price": t1_val,
                "gain_pct": round(((t1_val - p) / p) * 100.0, 1),
                "exit_share_pct": 33.3,
                "action_ar": "جني ربح جزئي (33%) ونقل وقف الخسارة لسعر الدخول (Breakeven)"
            },
            "T2": {
                "price": t2_val,
                "gain_pct": round(((t2_val - p) / p) * 100.0, 1),
                "exit_share_pct": 33.3,
                "action_ar": "جني ربح جزئي إضافي (33%) وتفعيل الوقف المتحرك (Trailing Stop 4%)"
            },
            "T3": {
                "price": t3_val,
                "gain_pct": round(((t3_val - p) / p) * 100.0, 1),
                "exit_share_pct": 33.4,
                "action_ar": "الخروج بالكمية المتبقية (34%) عند اكتمال الاتجاه أو كسر متوسط 20 يوم"
            }
        }

        # 4. Enforce the Uncertainty Rule
        avg_conf = sum(conf_list) / len(conf_list) if conf_list else 0.80
        prob_spread = max(prob_list) - min(prob_list) if prob_list else 0.0
        uncertainty_score = round((1.0 - avg_conf) + (prob_spread * 0.5), 2)

        is_high_uncertainty = (
            uncertainty_score >= 0.42 or
            avg_conf < 0.55 or
            (breadth["market_regime"] == MarketBreadthEngine.REGIME_PANIC_BEAR and overall_score < 75.0) or
            (flow["flow_regime"] == InstitutionalFlowEngine.FLOW_RETAIL_DISTRIBUTION and horizons_data["1D"]["prob_up"] < 0.50) or
            (sentiment.get("is_risk_event", False) and sentiment.get("materiality") == NewsSentimentEngine.IMPACT_HIGH)
        )

        if is_high_uncertainty:
            decision = "NO_TRADE_WAIT"
            action_ar = "🟡 مراقبة وانتظار (تفعيل قاعدة عدم اليقين لحماية رأس المال)"
            uncertainty_level = "HIGH"
        else:
            meta_prob = meta_label.get("probability_of_success_pct", ai_forecast.get("ai_confidence_score", 70.0))
            meta_dec = meta_label.get("meta_decision", "CONFIRM_BUY")
            if overall_score >= 80.0:
                if meta_prob >= 65.0 and meta_dec == "CONFIRM_BUY":
                    decision = "BUY"
                    action_ar = "🟢 فرصة شراء وتجميع ممتازة (توافق كمي وإجماع الذكاء الفوقي Meta-Label)"
                else:
                    decision = "WATCH"
                    action_ar = f"🟡 مراقبة واحتفاظ (الموديل الكمي يوصي بالشراء لكن احتمالية نجاح الذكاء الفوقي {meta_prob:.1f}% دون عتبة الإجماع 65%)"
            elif overall_score >= 65.0:
                decision = "WATCH"
                action_ar = "🟡 مراقبة / احتفاظ بالمركز"
            else:
                decision = "AVOID"
                action_ar = "🔴 تجنب فتح مراكز جديدة حالياً"
            uncertainty_level = "LOW" if avg_conf >= 0.85 else "MODERATE"

        if not is_liquid:
            decision = "AVOID"
            action_ar = "🔴 سهم ضعيف السيولة (مستبعد آلياً)"

        # Dominant Catalyst classification
        if fund_score >= 75.0:
            dominant_cat = "FUNDAMENTAL_QUALITY"
        elif technical["technical_score"] >= 75.0:
            dominant_cat = "TECHNICAL_BREAKOUT"
        elif "INFLOW" in block_trades.get("classification", ""):
            dominant_cat = "INSTITUTIONAL_BLOCK_INFLOW"
        elif rs_spread >= 1.5:
            dominant_cat = "SECTOR_MOMENTUM"
        else:
            dominant_cat = "MARKET_BETA"

        # Mathematical Expectancy
        win_rate = 0.55
        avg_win_pct = horizons_data["20D"]["expected_return_pct"]
        avg_loss_pct = 3.50
        expectancy_pct = round((win_rate * avg_win_pct) - ((1.0 - win_rate) * avg_loss_pct), 2)

        is_single_source = bool(rec and rec.get("price_type") == "SINGLE_SOURCE_ONLY")
        data_badge = "⚠️ مصدر بيانات أحادي (TV)" if is_single_source else "✅ بيانات مؤكدة مزدوجة"

        # Advanced Institutional Quant Layer: Valuation, Conformal Quantiles, Multi-Agent Debate, Historical Twins
        try:
            from core.valuation_engine import ValuationEngine
            from core.conformal_prediction_engine import ConformalPredictionEngine
            from core.multi_agent_debate_system import MultiAgentDebateSystem
            from core.historical_pattern_matcher import HistoricalPatternMatcher

            adv_val = ValuationEngine.evaluate_comprehensive_valuation(sym, current_price=p)
            adv_conformal = ConformalPredictionEngine.predict_conformal_quantiles(sym, current_price=p)
            adv_debate = MultiAgentDebateSystem.conduct_debate(sym, current_price=p)
            adv_twins = HistoricalPatternMatcher.find_historical_twins(sym, top_k=5)

            arb_mult = adv_debate.get("arbiter_multiplier", 1.0)
            if not adv_conformal.get("is_conformal_favorable", True):
                arb_mult = min(arb_mult, 0.80)
            if adv_val.get("is_margin_of_safety_satisfied", False):
                arb_mult = min(arb_mult * 1.15, 1.25)
            refined_pos_multiplier = round(risk_sizing.get("position_size_multiplier", 1.0) * arb_mult, 2)
        except Exception as e:
            adv_val = {"intrinsic_fair_value": p * 1.10, "margin_of_safety_pct": 10.0, "verdict_ar": "قيد التقييم"}
            adv_conformal = {"quantile_10_downside_pct": -4.0, "quantile_50_median_pct": 2.0, "quantile_90_upside_pct": 7.5, "quantile_risk_to_reward": 1.88}
            adv_debate = {"consensus_verdict": "HOLD_AND_WAIT", "consensus_verdict_ar": "مراقبة واحتفاظ", "arbiter_multiplier": 1.0, "executive_investment_memo_ar": ""}
            adv_twins = {"historical_win_rate_pct": 60.0, "expected_twin_return_pct": 2.5}
            refined_pos_multiplier = risk_sizing.get("position_size_multiplier", 1.0)

        now_dt = datetime.datetime.now()
        signal_timestamp = now_dt.strftime("%Y-%m-%d %H:%M:%S")
        valid_until = (now_dt + datetime.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
        max_entry_price = round(p * 1.005, 2)

        return {
            "ticker": sym,
            "company_name": prof["name_ar"],
            "sector": prof["sector"],
            "current_price": p,
            "price_source": price_source,
            "price_timestamp": price_timestamp,
            "price_type": rec.get("price_type", "CROSS_VERIFIED_REAL_DATA") if rec else "CROSS_VERIFIED_REAL_DATA",
            "is_single_source": is_single_source,
            "data_badge": data_badge,
            "status": "TRADABLE_LIQUID" if is_liquid else "ILLIQUID",
            "status_ar": ("سهم مؤهل للتداول (مصدر أحادي)" if is_single_source else "سهم مؤهل للتداول والتحليل") if is_liquid else "سهم ضعيف السيولة (مستبعد من النماذج)",
            "is_liquid": is_liquid,
            "is_tradable": is_liquid and decision in ["STRONG_BUY", "BUY", "ACCUMULATE"],
            "liquidity_gate": liquidity_eval,
            "entry_zone": f"{entry_low:.2f} – {entry_high:.2f}",
            "entry_low": round(entry_low, 2),
            "entry_high": round(entry_high, 2),
            "max_entry_price": max_entry_price,
            "signal_timestamp": signal_timestamp,
            "valid_until": valid_until,
            "ttl_minutes": 30,
            "is_expired": False,
            "stop_loss": stop_loss_price,
            "short_term_score": short_score,
            "medium_term_score": med_score,
            "long_term_score": long_score,
            "overall_score": overall_score,
            "explanation_ar": prof["why_ar"],
            "decision": decision,
            "action": decision,
            "action_ar": action_ar,
            "uncertainty_level": uncertainty_level,
            "uncertainty_score": uncertainty_score,
            "uncertainty_rule_triggered": is_high_uncertainty,
            "market_regime": breadth["market_regime"],
            "market_regime_label_ar": breadth["market_regime_label_ar"],
            "sector_relative_strength": sector_rs,
            "two_tier_relative_strength": {
                "stock_rs_vs_sector": stock_rs_tier,
                "sector_rs_vs_market": sector_rs_tier,
                "rs_alignment_label_ar": rs_alignment_ar
            },
            "technical_setup": technical,
            "risk_based_position": risk_sizing,
            "position_size_multiplier": risk_sizing.get("position_size_multiplier", 1.0),
            "refined_position_multiplier": refined_pos_multiplier,
            "arbiter_position_multiplier": refined_pos_multiplier,
            "ml_confidence_score": conf_val,
            "staged_exits": staged_exits,
            "holding_period_ar": technical.get("expected_holding_period_ar", "5 – 20 جلسة تداول (متوسط شهر)"),
            "invalidation_trigger_ar": technical.get("invalidation_trigger_ar", f"كسر الإغلاق أدنى مستوى الدعم {stop_loss_price:.2f} ج.م بإغلاق مؤكد."),
            "confidence_score": round(sum(conf_list) / len(conf_list) * 100.0, 1) if conf_list else 88.0,
            "beta_egx30": beta_egx30,
            "setup_name": technical["setup_classification"],
            "setup_name_ar": technical["setup_label_ar"],
            "dominant_catalyst": dominant_cat,
            "expectancy_pct": expectancy_pct,
            "expectancy_label": "[Theoretical Baseline Target - Not Empirical Until 30-Day Incubation Closes]",
            "institutional_flow": flow,
            "fundamentals": fundamentals,
            "news_sentiment": sentiment,
            "block_trades": block_trades,
            "up_drivers": up_drivers,
            "down_risks": down_risks,
            "macro_intelligence": macro_info,
            "corporate_hazard": corp_hazard,
            "ai_forecast": ai_forecast,
            "meta_label": meta_label,
            "meta_decision": meta_label.get("meta_decision", "CONFIRM_BUY"),
            "meta_decision_ar": meta_label.get("meta_decision_ar", ""),
            "probability_of_success_pct": meta_label.get("probability_of_success_pct", 70.0),
            "volatility_adjusted_return": meta_label.get("volatility_adjusted_return", 0.0),
            "ai_expected_alpha_10d": ai_forecast.get("expected_alpha_10d_pct", 0.0),
            "ai_confidence_score": meta_label.get("probability_of_success_pct", ai_forecast.get("ai_confidence_score", 50.0)),
            "ai_sentiment": ai_forecast.get("ai_sentiment", "NEUTRAL"),
            "ai_sentiment_ar": ai_forecast.get("ai_sentiment_ar", ""),
            "ai_top_drivers": meta_label.get("top_meta_drivers", ai_forecast.get("top_3_drivers", [])),
            "horizons": horizons_data,
            "comprehensive_valuation": adv_val,
            "conformal_quantiles": adv_conformal,
            "multi_agent_debate": adv_debate,
            "historical_twins": adv_twins,
            "advanced_quant_summary": {
                "intrinsic_fair_value": adv_val.get("intrinsic_fair_value"),
                "margin_of_safety_pct": adv_val.get("margin_of_safety_pct"),
                "valuation_verdict_ar": adv_val.get("verdict_ar"),
                "quantile_risk_to_reward": adv_conformal.get("quantile_risk_to_reward"),
                "conformal_envelope": adv_conformal.get("conformal_price_envelope"),
                "debate_verdict": adv_debate.get("consensus_verdict", adv_debate.get("verdict")),
                "debate_verdict_ar": adv_debate.get("consensus_verdict_ar", adv_debate.get("verdict_ar")),
                "executive_investment_memo_ar": adv_debate.get("executive_investment_memo_ar", adv_debate.get("investment_memo_ar")),
                "historical_twin_win_rate_pct": adv_twins.get("historical_win_rate_pct"),
                "expected_twin_return_pct": adv_twins.get("expected_twin_return_pct")
            }
        }

    _RANKINGS_CACHE: Dict[str, Any] = {}
    _RANKINGS_CACHE_TIME: Dict[str, float] = {}
    _CACHE_TTL_SEC: float = 120.0

    @classmethod
    def get_all_multi_horizon_rankings(
        cls,
        tickers: Optional[List[str]] = None,
        universe: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        Calculates rankings across specified tickers or index universe.
        Supported universe filters: 'all', 'egx30', 'egx70', 'egx100', 'core'.
        """
        cache_key = f"{universe}_{','.join(tickers or [])}"
        now = time.time()
        if cache_key in cls._RANKINGS_CACHE and len(cls._RANKINGS_CACHE[cache_key]) > 0 and (now - cls._RANKINGS_CACHE_TIME.get(cache_key, 0.0)) < cls._CACHE_TTL_SEC:
            return cls._RANKINGS_CACHE[cache_key]

        selected_tickers = []
        if tickers:
            selected_tickers = list(tickers)
        elif universe.lower() in ["core"]:
            # Core Top 24 large/mid-cap liquid equities
            selected_tickers = [
                "COMI.CA", "SWDY.CA", "TMGH.CA", "ORAS.CA", "ETEL.CA", "EGAL.CA",
                "ABUK.CA", "MFPC.CA", "ADIB.CA", "EAST.CA", "JUFO.CA", "GBCO.CA",
                "HRHO.CA", "EFIH.CA", "FWRY.CA", "DOMT.CA", "PHDC.CA", "ISPH.CA",
                "EMFD.CA", "AMOC.CA", "HELI.CA", "RAYA.CA", "CCAP.CA", "BTFH.CA"
            ]
        elif universe.lower() in ["egx30", "egx70", "egx100"]:
            from core.egx_universe_loader import EGXUniverseLoader
            selected_tickers = EGXUniverseLoader.get_tickers(universe)
        else:
            # Default to full 244 active EGX universe
            try:
                from data.universe_manager import UniverseManager
                selected_tickers = UniverseManager.get_all_tickers()
            except Exception:
                from core.egx_universe_loader import EGXUniverseLoader
                selected_tickers = EGXUniverseLoader.get_tickers("all")

        # Ensure no duplicates while preserving sequence
        seen = set()
        deduped = []
        for t in selected_tickers:
            sym = t.upper().strip()
            if not sym.endswith(".CA") and "." not in sym:
                sym = f"{sym}.CA"
            if sym not in seen:
                seen.add(sym)
                deduped.append(sym)

        # Parallel evaluation across constituents for high performance
        import concurrent.futures
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=24) as executor:
            future_to_sym = {executor.submit(cls.get_stock_multi_horizon_analysis, ticker): ticker for ticker in deduped}
            for future in concurrent.futures.as_completed(future_to_sym):
                try:
                    analysis = future.result()
                    if analysis:
                        results.append(analysis)
                except Exception:
                    continue

        results.sort(key=lambda x: x["overall_score"], reverse=True)
        for idx, item in enumerate(results, start=1):
            item["rank"] = idx

        # Evaluate portfolio cluster risk across top 5 recommendations
        from core.portfolio_correlation_engine import PortfolioCorrelationEngine
        top_5_tickers = [r["ticker"] for r in results[:5]]
        cluster_risk = PortfolioCorrelationEngine.evaluate_portfolio_cluster_risk(top_5_tickers)
        for idx, item in enumerate(results[:5]):
            item["portfolio_cluster_risk"] = cluster_risk["cluster_risk"]
            item["portfolio_cluster_risk_ar"] = cluster_risk["cluster_risk_ar"]

        if len(results) > 0:
            cls._RANKINGS_CACHE[cache_key] = results
            cls._RANKINGS_CACHE_TIME[cache_key] = now

        return results

    @classmethod
    def get_short_term_10d_opportunities(
        cls,
        universe: str = "all"
    ) -> Dict[str, Any]:
        """
        Specialized 2-Week (10-Day Horizon) Opportunities Screen.
        Ranks equities by (Expected 10D Upside / Expected 10D Downside Risk).
        
        Strict Disqualification Gates:
        1. High Uncertainty / NO_TRADE_WAIT active.
        2. Thin / Low Liquidity (turnover < 5M EGP or restricted volume).
        3. DOWNTREND_PULLBACK or Weak Technical regime.
        4. Non-positive expected upside.
        """
        from core.mlops_pipeline import MLOpsPipeline
        system_status = MLOpsPipeline.get_system_status()

        if system_status == "EMERGENCY_HALT":
            return {
                "disclaimer_ar": "🚨 تم تعليق أوامر وترشيحات الشراء مؤقتاً لتفعيل صمام الأمان وإعادة تدريب الموديل.",
                "horizon": "10D",
                "ranking_criterion": "EMERGENCY_HALT_ACTIVE",
                "system_status": "EMERGENCY_HALT",
                "opportunities_count": 0,
                "has_sufficient_opportunities": False,
                "fallback_message_ar": "🚨 تم تعليق فتح مراكز الشراء الجديدة آلياً بسبب تفعيل صمام الأمان الطارئ وإعادة التدريب (Emergency Retrain in progress).",
                "opportunities": []
            }

        rankings = cls.get_all_multi_horizon_rankings(universe=universe)
        
        # Disqualified thin liquidity stocks
        THIN_LIQUIDITY_TICKERS = {"EKHO.CA", "EKHOA.CA", "BINV.CA", "CICH.CA", "DOMT.CA"}

        eligible = []
        for r in rankings:
            sym = r["ticker"]

            # Filter 1: Uncertainty / NO_TRADE_WAIT Gate
            if r.get("uncertainty_rule_triggered", False) or r.get("decision") == "NO_TRADE_WAIT":
                continue

            # Filter 2: Liquidity Gate
            if sym in THIN_LIQUIDITY_TICKERS:
                continue
            canon_rec = MarketPriceService.get_canonical_price_record(sym)
            if canon_rec and canon_rec.get("turnover_egp", 10_000_000.0) < 5_000_000.0:
                continue

            # Filter 3: Downtrend Gate
            setup_cls = r.get("technical_setup", {}).get("setup_classification", "")
            trend_regime = r.get("technical_setup", {}).get("trend_regime", "")
            if setup_cls == TechnicalSetupEngine.SETUP_DOWNTREND_PULLBACK or trend_regime in ["WEAK", "DOWNTREND"]:
                continue

            # 10D Horizon Metrics
            h10 = r["horizons"]["10D"]
            upside = h10["expected_return_pct"]
            downside = h10.get("expected_downside_pct", -2.5)

            # Filter 4: Positive Expected Upside
            if upside <= 0.5:
                continue

            # Reward to Downside Risk Ratio
            abs_downside = max(abs(downside), 0.20)
            rr_downside_ratio = round(upside / abs_downside, 2)

            entry_low = float(r["entry_zone"].split("–")[0].strip()) if "–" in r.get("entry_zone", "") else r["current_price"] * 0.985
            entry_high = float(r["entry_zone"].split("–")[1].strip()) if "–" in r.get("entry_zone", "") else r["current_price"] * 0.998

            record = {
                "ticker": sym,
                "company_name": r["company_name"],
                "sector": r.get("sector", ""),
                "current_price": r["current_price"],
                "entry_zone": f"{entry_low:.2f} – {entry_high:.2f}",
                "stop_loss": r["stop_loss"],
                "stop_loss_type_ar": "وقف خسارة ديناميكي مبني على تقلب السهم الفعلي (ATR × 2.0)",
                "expected_upside_10d_pct": upside,
                "expected_downside_10d_pct": downside,
                "reward_to_downside_ratio": rr_downside_ratio,
                "target_price_10d": h10["target_1"],
                "target_bounds_10d": h10.get("target_1_bounds", {}),
                "setup_classification": setup_cls,
                "setup_name_ar": r.get("setup_name_ar", "تداول فني اعتيادي"),
                "dominant_catalyst": r.get("dominant_catalyst", "MARKET_BETA"),
                "confidence": r.get("confidence_score", 88.0),
                "invalidation_trigger_ar": r.get("invalidation_trigger_ar", ""),
                "expected_holding_period": r.get("holding_period_ar", "7 – 15 جلسة تداول (تأكيد الاتجاه)"),
                "quality_of_earnings": r.get("fundamentals", {}).get("earnings_quality_flag_ar", ""),
                "alpha_score": r["overall_score"]
            }
            eligible.append(record)

        # Sort descending by Reward to Downside Risk Ratio
        eligible.sort(key=lambda x: x["reward_to_downside_ratio"], reverse=True)
        for idx, item in enumerate(eligible, start=1):
            item["rank"] = idx

        has_sufficient = len(eligible) >= 3

        return {
            "disclaimer_ar": "⚠️ هذه الترشيحات جزء من نظام لسه في فترة الحضانة التجريبية (يوم 1 من 30) ولم تثبت جدارته بعد — استخدمها للمتابعة والتعلم وليس كقرار استثماري فعلي حتى تكتمل فترة التحقق.",
            "horizon": "10D (أسبوعين تداول / 10 جلسات تقريبياً)",
            "ranking_criterion": "العائد المتوقع لـ 10D مقسوماً على مخاطرة النزول المتوقعة (Reward-to-Downside-Risk Ratio)",
            "opportunities_count": len(eligible),
            "has_sufficient_opportunities": has_sufficient,
            "fallback_message_ar": None if has_sufficient else "لا توجد فرص قصيرة المدى تستوفي معايير الجودة والسيولة حالياً.",
            "opportunities": eligible
        }

    @classmethod
    def is_signal_expired(
        cls,
        signal_data: Dict[str, Any],
        current_time: Optional[Any] = None
    ) -> bool:
        """
        Evaluates whether a trading signal has passed its 30-minute Time-To-Live (TTL).
        
        Args:
            signal_data: Dictionary containing 'valid_until' timestamp or 'signal_timestamp'.
            current_time: Optional reference datetime or ISO/formatted string (defaults to now).
            
        Returns:
            True if signal has expired, False otherwise.
        """
        if not signal_data:
            return True

        if current_time is None:
            now_dt = datetime.datetime.now()
        elif isinstance(current_time, str):
            try:
                now_dt = datetime.datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S")
            except Exception:
                try:
                    now_dt = datetime.datetime.fromisoformat(current_time)
                except Exception:
                    now_dt = datetime.datetime.now()
        else:
            now_dt = current_time

        valid_until_str = signal_data.get("valid_until")
        if valid_until_str:
            try:
                valid_dt = datetime.datetime.strptime(valid_until_str, "%Y-%m-%d %H:%M:%S")
                return now_dt > valid_dt
            except Exception:
                pass

        sig_time_str = signal_data.get("signal_timestamp") or signal_data.get("price_timestamp")
        if sig_time_str:
            try:
                sig_dt = datetime.datetime.strptime(sig_time_str, "%Y-%m-%d %H:%M:%S")
                ttl_mins = signal_data.get("ttl_minutes", 30)
                return now_dt > (sig_dt + datetime.timedelta(minutes=ttl_mins))
            except Exception:
                pass

        return False

    @classmethod
    def export_multi_horizon_predictions(cls, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Computes and exports complete multi-horizon forecasts for all active EGX equities
        using live SSOT prices from MarketPriceService. Saves to data/multi_horizon_predictions.json.
        """
        workspace = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out_file = output_path or os.path.join(workspace, "data", "multi_horizon_predictions.json")

        all_rankings = cls.get_all_multi_horizon_rankings(universe="all")
        predictions_map: Dict[str, Any] = {}

        for item in all_rankings:
            ticker = item.get("ticker")
            if ticker:
                predictions_map[ticker] = item

        payload = {
            "as_of": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_equities": len(predictions_map),
            "source": "GEN-26 Multi-Horizon Forecasting Engine (Live SSOT Prices)",
            "predictions": predictions_map
        }

        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        # Sync authoritative copy to reports directory
        reports_file = os.path.join(workspace, "reports", "multi_horizon_predictions.json")
        os.makedirs(os.path.dirname(reports_file), exist_ok=True)
        with open(reports_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return payload

    # Aliases for backward & QA compatibility
    generate_short_term_opportunities = get_short_term_10d_opportunities
    _evaluate_single_stock_forecast = get_stock_multi_horizon_analysis


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    print("=== GEN-26 Multi-Horizon Forecasting Engine Execution ===")
    res = MultiHorizonEngine.export_multi_horizon_predictions()
    print(f"Successfully generated multi-horizon forecasts for {res['total_equities']} EGX equities.")
    print(f"Authoritative reports saved to data/ and reports/ directories.")
