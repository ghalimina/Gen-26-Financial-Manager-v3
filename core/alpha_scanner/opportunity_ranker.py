#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, json, logging, time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from core.market_price_service import MarketPriceService
from core.trade_selection_model import TradeSelectionModel
from .multi_layer_scanner import MultiLayerScanner
from .alpha_scorer import AlphaScorer

logger = logging.getLogger("GEN26.OpportunityRanker")

class OpportunityRanker:
    """
    Parallel Universe Scanner & Opportunity Ranking Engine for EGX Equities.
    """

    @classmethod
    def evaluate_stock_scan(cls, ticker: str, regime: str = "BULL_EXPANSION") -> Optional[Dict[str, Any]]:
        stock_rec = MultiLayerScanner.get_stock_ranking_record(ticker)
        rec = MarketPriceService.get_canonical_price_record(ticker)
        if stock_rec and stock_rec.get("current_price"):
            price = float(stock_rec["current_price"])
            name_ar = stock_rec.get("company_name") or stock_rec.get("name_ar", ticker)
            sector = stock_rec.get("sector", "General")
        elif rec and rec.get("price"):
            price = float(rec["price"])
            name_ar = rec.get("name_ar", ticker)
            sector = rec.get("sector", "General")
        else:
            price = 100.0
            name_ar = ticker
            sector = "General"

        scan_res = MultiLayerScanner.scan_single_stock(ticker, price, regime, stock_rec=stock_rec)
        scored_res = AlphaScorer.calculate_alpha_score(scan_res)

        trade_gate = TradeSelectionModel.evaluate_trade_eligibility(
            ticker=ticker,
            expected_return_pct=scored_res["expected_return_pct"],
            uncertainty_score=scored_res["uncertainty_score"],
            market_regime=regime
        )

        return {
            "ticker": ticker,
            "name_ar": name_ar,
            "sector": sector,
            "current_price": price,
            "alpha_score": scored_res["alpha_score"],
            "win_prob": scored_res["win_prob"],
            "win_probability_pct": scored_res["win_probability_pct"],
            "expected_return": scored_res["expected_return"],
            "expected_return_pct": scored_res["expected_return_pct"],
            "uncertainty_score": scored_res["uncertainty_score"],
            "opportunity_score": scored_res["opportunity_score"],
            "net_edge_pct": trade_gate.get("net_edge_pct", round(scored_res["expected_return_pct"] - 0.94 - (scored_res["uncertainty_score"] * 1.5), 2)),
            "tier": scored_res["tier"],
            "tier_ar": scored_res["tier_ar"],
            "action_verdict": scored_res["action_verdict"],
            "is_tradeable": trade_gate.get("is_tradeable", scored_res["alpha_score"] >= 65.0),
            "layer_scores": scored_res["layer_scores"],
            "scan_details": scan_res
        }

    @classmethod
    def scan_universe(cls, universe_filter: str = "all", regime: str = "BULL_EXPANSION") -> Dict[str, Any]:
        from core.egx_universe_loader import EGXUniverseLoader
        tickers = EGXUniverseLoader.get_tickers("all")

        results = []
        for t in tickers:
            try:
                res = cls.evaluate_stock_scan(t, regime=regime)
                if res:
                    results.append(res)
            except Exception as e:
                logger.debug(f"Scan error for {t}: {e}")

        # High quality stocks appear at the top, descending down to weaker stocks
        results.sort(key=lambda x: (x["alpha_score"], x["expected_return_pct"], x["win_probability_pct"]), reverse=True)

        for i, item in enumerate(results, 1):
            item["rank"] = i

        candidates_count = sum(1 for x in results if x["alpha_score"] >= 70.0)
        high_conviction_count = sum(1 for x in results if x["alpha_score"] >= 75.0)

        return {
            "scan_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+03:00"),
            "regime": regime,
            "total_scanned": len(results),
            "candidates_count": candidates_count,
            "high_conviction_count": high_conviction_count,
            "opportunities": results
        }

