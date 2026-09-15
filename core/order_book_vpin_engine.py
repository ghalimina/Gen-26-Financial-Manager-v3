#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/order_book_vpin_engine.py — Limit Order Book (LOB) & VPIN Toxicity Engine
# 1. Level 2 LOB State & Micro-Price Estimation.
# 2. Order Flow Imbalance (OFI) tracking.
# 3. Volume-Synchronized Probability of Toxicity (VPIN - Easley, López de Prado, O'Hara).
#    Signals toxic adverse selection and predatory iceberg algorithmic sweeps.
# =============================================================================

import math
import numpy as np
from typing import Dict, List, Any, Optional, Tuple


class OrderBookVpinEngine:
    """
    Microstructure analytics engine for Level 2 Order Book Depth & VPIN Toxicity.
    """

    @classmethod
    def analyze_order_book_depth(
        cls,
        bids: List[Tuple[float, int]],
        asks: List[Tuple[float, int]]
    ) -> Dict[str, Any]:
        """
        Computes LOB Level 2 depth metrics:
        - Best Bid / Ask and Spread
        - Spread in Basis Points (bps)
        - Depth Imbalance Ratio
        - Micro-Price (Volume-weighted mid-price)
        """
        if not bids or not asks:
            return {
                "valid": False,
                "error": "Empty bids or asks queues"
            }

        # Ensure sorted: bids descending, asks ascending
        sorted_bids = sorted(bids, key=lambda x: x[0], reverse=True)
        sorted_asks = sorted(asks, key=lambda x: x[0])

        best_bid, best_bid_vol = sorted_bids[0]
        best_ask, best_ask_vol = sorted_asks[0]

        spread = best_ask - best_bid
        mid_price = (best_ask + best_bid) / 2.0
        spread_bps = (spread / max(mid_price, 1e-4)) * 10000.0

        # Micro-price calculation: Volume weighted toward the side with less liquidity
        tot_top_vol = best_bid_vol + best_ask_vol
        if tot_top_vol > 0:
            micro_price = (best_bid_vol * best_ask + best_ask_vol * best_bid) / tot_top_vol
        else:
            micro_price = mid_price

        # Top 5 levels aggregate depth
        total_bid_depth = sum(vol for _, vol in sorted_bids[:5])
        total_ask_depth = sum(vol for _, vol in sorted_asks[:5])
        tot_depth = total_bid_depth + total_ask_depth
        imbalance_ratio = (total_bid_depth - total_ask_depth) / max(tot_depth, 1)

        return {
            "valid": True,
            "best_bid": round(best_bid, 2),
            "best_ask": round(best_ask, 2),
            "mid_price": round(mid_price, 2),
            "micro_price": round(micro_price, 2),
            "spread": round(spread, 2),
            "spread_bps": round(spread_bps, 1),
            "total_bid_depth": total_bid_depth,
            "total_ask_depth": total_ask_depth,
            "imbalance_ratio": round(imbalance_ratio, 3),
            "pressure": "BUY_PRESSURE" if imbalance_ratio > 0.20 else ("SELL_PRESSURE" if imbalance_ratio < -0.20 else "BALANCED")
        }

    @classmethod
    def calculate_vpin(
        cls,
        trade_sizes: List[int],
        trade_prices: List[float],
        bucket_volume: int = 50000,
        num_buckets: int = 20
    ) -> Dict[str, Any]:
        """
        Calculates Volume-Synchronized Probability of Toxicity (VPIN):
        - Partitions trade flow into constant-volume buckets of size V.
        - Signs volume into Buy Volume (V_B) and Sell Volume (V_S) using tick rule / price movement.
        - Imbalance in bucket tau: |V_B - V_S|.
        - VPIN = sum(|V_B - V_S|) / (N * V).
        """
        if len(trade_sizes) < 2 or len(trade_prices) < 2:
            return {
                "vpin": 0.25,
                "toxicity_regime": "LOW_TOXICITY",
                "is_toxic": False,
                "buckets_count": 0
            }

        # 1. Sign volume using tick rule
        signed_volumes = []  # positive = buy, negative = sell
        for i in range(len(trade_sizes)):
            sz = trade_sizes[i]
            if i == 0:
                sign = 1
            else:
                p_curr = trade_prices[i]
                p_prev = trade_prices[i - 1]
                if p_curr > p_prev:
                    sign = 1
                elif p_curr < p_prev:
                    sign = -1
                else:
                    sign = signed_volumes[-1][0] if signed_volumes else 1
            signed_volumes.append((sign, sz))

        # 2. Fill volume buckets
        bucket_imbalances = []
        current_buy_vol = 0
        current_sell_vol = 0
        current_accum = 0

        for sign, sz in signed_volumes:
            remaining_sz = sz
            while remaining_sz > 0:
                space = bucket_volume - current_accum
                alloc = min(remaining_sz, space)
                if sign > 0:
                    current_buy_vol += alloc
                else:
                    current_sell_vol += alloc
                current_accum += alloc
                remaining_sz -= alloc

                # Bucket filled
                if current_accum >= bucket_volume:
                    imb = abs(current_buy_vol - current_sell_vol)
                    bucket_imbalances.append(imb)
                    current_buy_vol = 0
                    current_sell_vol = 0
                    current_accum = 0

        if not bucket_imbalances:
            # Fallback if volume didn't fill one full bucket
            vpin_val = 0.20
            regime = "LOW_TOXICITY"
        else:
            recent_imbalances = bucket_imbalances[-num_buckets:]
            vpin_val = sum(recent_imbalances) / (len(recent_imbalances) * bucket_volume)
            vpin_val = min(max(vpin_val, 0.0), 1.0)

            if vpin_val >= 0.65:
                regime = "EXTREME_TOXICITY_ALERT"
            elif vpin_val >= 0.45:
                regime = "ELEVATED_TOXICITY"
            else:
                regime = "NORMAL_LIQUIDITY"

        return {
            "vpin": round(vpin_val, 4),
            "vpin_pct": round(vpin_val * 100.0, 2),
            "toxicity_regime": regime,
            "is_toxic": vpin_val >= 0.50,
            "buckets_evaluated": len(bucket_imbalances),
            "warning_ar": (
                "تحذير سيولة سامة: احتمال وجود صفقات عكسية لمضارب مطلع أو بيع مؤسسي مخفي."
                if vpin_val >= 0.50 else "تدفق سيولة طبيعي ومتزن."
            )
        }
