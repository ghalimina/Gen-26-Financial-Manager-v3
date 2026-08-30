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
        rec = MarketPriceService.get_canonical_price_record(ticker)
        if not rec or not rec.get("price"):
            price = 100.0
            name_ar = ticker
            sector = "General"
        else:
            price = rec["price"]
            name_ar = rec.get("name_ar", ticker)
            sector = rec.get("sector", "General")

        scan_res = MultiLayerScanner.scan_single_stock(ticker, price, regime)
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
            "win_probability_pct": scored_res["win_probability_pct"],
            "expected_return_pct": scored_res["expected_return_pct"],
            "uncertainty_score": scored_res["uncertainty_score"],
            "opportunity_score": scored_res["opportunity_score"],
            "net_edge_pct": trade_gate["net_edge_pct"],
            "tier": scored_res["tier"],
            "tier_ar": scored_res["tier_ar"],
            "action_verdict": scored_res["action_verdict"],
            "is_tradeable": trade_gate["is_tradeable"],
            "layer_scores": scored_res["layer_scores"],
            "scan_details": scan_res
        }

    @classmethod
    def scan_universe(cls, universe_filter: str = "all", regime: str = "BULL_EXPANSION") -> Dict[str, Any]:
        from core.egx_universe_loader import EGXUniverseLoader
        tickers = EGXUniverseLoader.get_tickers("all")

        results = []
        with ThreadPoolExecutor(max_workers=16) as executor:
            futures = {executor.submit(cls.evaluate_stock_scan, t, regime): t for t in tickers}
            for f in futures:
                try:
                    res = f.result()
                    if res:
                        results.append(res)
                except Exception:
                    pass

        results.sort(key=lambda x: (x["opportunity_score"], x["alpha_score"]), reverse=True)

        for i, item in enumerate(results, 1):
            item["rank"] = i

        candidates_count = sum(1 for x in results if x["alpha_score"] >= 70.0)
        high_conviction_count = sum(1 for x in results if x["alpha_score"] >= 85.0)

        return {
            "scan_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+03:00"),
            "regime": regime,
            "total_scanned": len(results),
            "candidates_count": candidates_count,
            "high_conviction_count": high_conviction_count,
            "opportunities": results
        }
