"""
research_v42/engines/master_stock_ranker.py

Master Stock Ranker — GEN-26 V42 Research Layer
Aggregates all sub-engines into a single MasterScore (0–100).

Weights (configurable — NOT optimized on test set):
  Fundamental Quality  = 30%
  Valuation            = 20%
  Technical Timing     = 15%
  Liquidity            = 10%
  Sector               = 10%
  Macro                = 10%
  ML Shadow            = 5%   (only if ML_MODE != OFF)

RULE: V42 MasterScore feeds the DecisionObject.
      V4.1 Risk Gates remain authoritative over execution.

STATUS: RESEARCH / SHADOW
"""
from __future__ import annotations
import sys
import os
import math
import datetime
import json
from dataclasses import dataclass, field
from typing import Optional

# Engine imports (same package)
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from fundamental_engine import FundamentalEngine
from valuation_engine import ValuationEngine
from technical_timing_engine import TechnicalTimingEngine
from market_regime_engine import MarketRegimeEngine
from sector_macro_liquidity_engines import SectorEngine, MacroEngine, LiquidityEngine

# ML Shadow weight config
ML_MODE = "SHADOW"  # OFF | SHADOW | CONFIDENCE_ONLY | ACTIVE

WEIGHTS = {
    "fundamental": 0.30,
    "valuation":   0.20,
    "technical":   0.15,
    "liquidity":   0.10,
    "sector":      0.10,
    "macro":       0.10,
    "ml_shadow":   0.05,
}


@dataclass
class StockScore:
    ticker: str
    company_name: str = "UNKNOWN"
    sector: str = "UNKNOWN"
    current_price: Optional[float] = None

    # Sub-scores (0–100)
    fundamental_score: float = 50.0
    valuation_score: float = 50.0
    technical_score: float = 50.0
    liquidity_score: float = 50.0
    sector_score: float = 50.0
    macro_score: float = 50.0
    ml_shadow_score: float = 50.0

    # Composite
    master_score: float = 50.0

    # Qualitative summary
    valuation_label: str = "UNKNOWN"
    liquidity_label: str = "UNKNOWN"
    market_regime: str = "UNKNOWN"
    trend_direction: str = "UNKNOWN"
    is_valid_pullback: bool = False
    volatility_regime: str = "UNKNOWN"

    # Top drivers
    top_positives: list = field(default_factory=list)
    top_negatives: list = field(default_factory=list)
    all_warnings: list = field(default_factory=list)

    # Data quality
    data_quality: str = "PROXY"
    missing_count: int = 0
    confidence: float = 0.0

    # Timestamps
    computed_at: str = ""


class MasterStockRanker:
    """
    Orchestrates all V42 engines and produces a ranked StockScore for each ticker.
    """

    def __init__(self):
        self.fundamental_engine = FundamentalEngine()
        self.valuation_engine = ValuationEngine()
        self.technical_engine = TechnicalTimingEngine()
        self.regime_engine = MarketRegimeEngine()
        self.sector_engine = SectorEngine()
        self.macro_engine = MacroEngine()
        self.liquidity_engine = LiquidityEngine()

        # Get market regime once per session
        self._regime = None

    def _get_regime(self):
        if self._regime is None:
            self._regime = self.regime_engine.classify()
        return self._regime

    def rank_ticker(self, ticker: str) -> StockScore:
        score = StockScore(ticker=ticker)
        score.computed_at = datetime.datetime.utcnow().isoformat() + "Z"
        all_warnings = []

        # ── Sector ──────────────────────────────────────────────
        sec = self.sector_engine.score(ticker)
        score.company_name = sec.company_name
        score.sector = sec.sector
        score.sector_score = sec.sector_score
        all_warnings.extend(sec.warnings)

        # ── Fundamental ─────────────────────────────────────────
        try:
            fund = self.fundamental_engine.score(ticker)
            score.fundamental_score = fund.fundamental_score
            score.missing_count += len(fund.missing_metrics)
            all_warnings.extend(fund.warnings[:3])
        except Exception as e:
            all_warnings.append(f"Fundamental engine error: {e}")

        # ── Valuation ───────────────────────────────────────────
        try:
            val = self.valuation_engine.fetch_valuation(ticker, sector=score.sector)
            score.valuation_score = val.valuation_score
            score.valuation_label = val.overall_valuation
            all_warnings.extend(val.warnings[:2])
        except Exception as e:
            all_warnings.append(f"Valuation engine error: {e}")

        # ── Technical Timing ────────────────────────────────────
        try:
            tech = self.technical_engine.compute(ticker)
            score.technical_score = tech.timing_score
            score.current_price = tech.current_price
            score.trend_direction = tech.trend_direction
            score.is_valid_pullback = tech.is_valid_pullback
            score.volatility_regime = tech.volatility_regime
            all_warnings.extend(tech.warnings[:2])
        except Exception as e:
            all_warnings.append(f"Technical engine error: {e}")

        # ── Liquidity ───────────────────────────────────────────
        try:
            liq = self.liquidity_engine.score(ticker)
            score.liquidity_score = liq.liquidity_score
            score.liquidity_label = liq.liquidity_label
            all_warnings.extend(liq.warnings[:2])
        except Exception as e:
            all_warnings.append(f"Liquidity engine error: {e}")

        # ── Macro ───────────────────────────────────────────────
        try:
            macro = self.macro_engine.get_macro()
            score.macro_score = macro.macro_score
            score.market_regime = self._get_regime().regime
        except Exception as e:
            all_warnings.append(f"Macro engine error: {e}")

        # ── ML Shadow (placeholder — 50 until real model connected) ─
        score.ml_shadow_score = 50.0  # Neutral until V42 models trained

        # ── Master Score ────────────────────────────────────────
        if ML_MODE == "OFF":
            # Redistribute ML weight proportionally
            w = dict(WEIGHTS)
            ml_w = w.pop("ml_shadow")
            total = sum(w.values())
            w = {k: v / total for k, v in w.items()}
        else:
            w = WEIGHTS

        master = (
            score.fundamental_score * w.get("fundamental", 0.30) +
            score.valuation_score   * w.get("valuation",   0.20) +
            score.technical_score   * w.get("technical",   0.15) +
            score.liquidity_score   * w.get("liquidity",   0.10) +
            score.sector_score      * w.get("sector",      0.10) +
            score.macro_score       * w.get("macro",       0.10) +
            score.ml_shadow_score   * w.get("ml_shadow",   0.05)
        )
        score.master_score = round(min(max(master, 0.0), 100.0), 1)

        # ── Confidence ──────────────────────────────────────────
        data_available = sum([
            score.fundamental_score != 50.0,
            score.valuation_score != 50.0,
            score.technical_score != 50.0,
            score.liquidity_score != 50.0,
        ])
        score.confidence = round(data_available / 4.0, 2)

        if score.confidence < 0.5:
            score.data_quality = "PARTIAL"
            all_warnings.append("Low data confidence — treat score with caution")

        # ── Drivers ─────────────────────────────────────────────
        sub_scores = {
            "📊 الأساسيات":  score.fundamental_score,
            "💰 التقييم":     score.valuation_score,
            "📈 التوقيت":     score.technical_score,
            "💧 السيولة":     score.liquidity_score,
            "🏭 القطاع":     score.sector_score,
            "🌍 الاقتصاد الكلي": score.macro_score,
        }
        ranked = sorted(sub_scores.items(), key=lambda x: x[1], reverse=True)
        score.top_positives = [f"{k} ({v:.0f}/100)" for k, v in ranked if v > 55][:3]
        score.top_negatives = [f"{k} ({v:.0f}/100)" for k, v in ranked if v < 45][:3]
        score.all_warnings = all_warnings[:10]

        return score

    def rank_all(self, tickers: list[str]) -> list[StockScore]:
        results = []
        for t in tickers:
            try:
                s = self.rank_ticker(t)
                results.append(s)
            except Exception as e:
                print(f"[ERROR] rank_ticker({t}): {e}")
        # Sort by master score descending
        results.sort(key=lambda x: x.master_score, reverse=True)
        return results


# ─────────────────────────────────────────────────────────
# Standalone runner
# ─────────────────────────────────────────────────────────
EGX_TICKERS = [
    "COMI.CA", "TMGH.CA", "SWDY.CA", "HRHO.CA", "FWRY.CA",
    "PHDC.CA", "ESRS.CA", "HELI.CA", "AMOC.CA", "ISPH.CA",
    "ETEL.CA", "ABUK.CA", "MFPC.CA",
]

if __name__ == "__main__":
    import sys
    tickers = sys.argv[1:] if len(sys.argv) > 1 else EGX_TICKERS

    print("=" * 80)
    print("🏛️ GEN-26 V42 — MASTER STOCK RANKER")
    print(f"   Tickers: {len(tickers)} | Mode: {ML_MODE} | DATA: YFinance PROXY")
    print("=" * 80)

    ranker = MasterStockRanker()
    ranked = ranker.rank_all(tickers)

    print(f"\n{'RANK':<4} {'TICKER':<10} {'COMPANY':<22} {'MASTER':>7} "
          f"{'FUND':>6} {'VAL':>6} {'TECH':>6} {'LIQ':>6} "
          f"{'REGIME':<12} {'PULLBACK'}")
    print("-" * 105)

    for i, s in enumerate(ranked, 1):
        pb = "✅" if s.is_valid_pullback else "❌"
        print(f"{i:<4} {s.ticker:<10} {s.company_name[:20]:<22} {s.master_score:>7.1f} "
              f"{s.fundamental_score:>6.1f} {s.valuation_score:>6.1f} "
              f"{s.technical_score:>6.1f} {s.liquidity_score:>6.1f} "
              f"{s.market_regime:<12} {pb}")

    # Save JSON report
    out = os.path.join(os.path.dirname(_HERE), "reports", "v42_ranking_latest.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    report = [
        {
            "rank": i + 1,
            "ticker": s.ticker,
            "company": s.company_name,
            "sector": s.sector,
            "master_score": s.master_score,
            "fundamental_score": s.fundamental_score,
            "valuation_score": s.valuation_score,
            "technical_score": s.technical_score,
            "liquidity_score": s.liquidity_score,
            "macro_score": s.macro_score,
            "sector_score": s.sector_score,
            "valuation_label": s.valuation_label,
            "liquidity_label": s.liquidity_label,
            "trend_direction": s.trend_direction,
            "is_valid_pullback": s.is_valid_pullback,
            "volatility_regime": s.volatility_regime,
            "market_regime": s.market_regime,
            "confidence": s.confidence,
            "data_quality": s.data_quality,
            "top_positives": s.top_positives,
            "top_negatives": s.top_negatives,
            "warnings": s.all_warnings[:5],
            "computed_at": s.computed_at,
        }
        for i, s in enumerate(ranked)
    ]
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"data_mode": "YFINANCE_PROXY", "ml_mode": ML_MODE, "stocks": report}, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Report saved: {out}")
