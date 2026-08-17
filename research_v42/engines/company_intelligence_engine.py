"""
research_v42/engines/company_intelligence_engine.py

Company Intelligence Engine — GEN-26 V42 Research Layer
Combines all engines into a complete company intelligence report.

Answers:
  1. ماذا يحدث الآن؟
  2. لماذا قد يصعد؟
  3. لماذا قد يهبط؟
  4. ما أفضل أفق؟
  5. ما المتوقع لكل أفق؟
  6. ما السيناريوهات؟
  7. ما الثقة؟
  8. هل البيانات موثوقة؟

STATUS: RESEARCH / SHADOW — Does NOT affect V4.1 execution
"""
from __future__ import annotations
import sys, os, json, datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from master_stock_ranker import MasterStockRanker, StockScore
from multi_horizon_forecast_engine import MultiHorizonForecastEngine, HORIZONS
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Scenario:
    label: str           # BULL | BASE | BEAR
    probability: float
    expected_return_pct: float
    key_drivers: list[str] = field(default_factory=list)


@dataclass
class CompanyReport:
    ticker: str
    company_name: str
    sector: str
    current_price: Optional[float]
    computed_at: str

    # Score summary
    master_score: float
    fundamental_score: float
    valuation_score: float
    technical_score: float
    liquidity_score: float
    macro_score: float
    sector_score: float
    valuation_label: str
    liquidity_label: str

    # Narrative
    up_drivers: list[str] = field(default_factory=list)
    down_risks: list[str] = field(default_factory=list)
    why_no_trade: list[str] = field(default_factory=list)

    # Forecasts
    forecasts: dict = field(default_factory=dict)   # {horizon: HorizonForecast dict}
    best_horizon: Optional[int] = None

    # Scenarios
    scenarios: list[Scenario] = field(default_factory=list)

    # Market context
    market_regime: str = "UNKNOWN"
    trend_direction: str = "UNKNOWN"
    volatility_regime: str = "UNKNOWN"
    is_valid_pullback: bool = False

    # Data quality
    data_quality: str = "PROXY"
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "company_name": self.company_name,
            "sector": self.sector,
            "current_price": self.current_price,
            "computed_at": self.computed_at,
            "data_mode": "YFINANCE_PROXY_DELAYED",
            "scores": {
                "master": self.master_score,
                "fundamental": self.fundamental_score,
                "valuation": self.valuation_score,
                "technical": self.technical_score,
                "liquidity": self.liquidity_score,
                "macro": self.macro_score,
                "sector": self.sector_score,
            },
            "labels": {
                "valuation": self.valuation_label,
                "liquidity": self.liquidity_label,
                "market_regime": self.market_regime,
                "trend": self.trend_direction,
                "volatility": self.volatility_regime,
            },
            "up_drivers": self.up_drivers,
            "down_risks": self.down_risks,
            "is_valid_pullback": self.is_valid_pullback,
            "forecasts": self.forecasts,
            "best_horizon_days": self.best_horizon,
            "scenarios": [
                {"label": s.label, "probability": s.probability,
                 "expected_return_pct": s.expected_return_pct,
                 "key_drivers": s.key_drivers}
                for s in self.scenarios
            ],
            "data_quality": self.data_quality,
            "confidence": self.confidence,
            "warnings": self.warnings[:8],
        }


class CompanyIntelligenceEngine:
    """
    Top-level orchestrator for V42 company intelligence.
    """

    def __init__(self):
        self.ranker = MasterStockRanker()
        self.forecast_engine = MultiHorizonForecastEngine()

    def _build_scenarios(self, score: StockScore, forecasts: dict) -> list[Scenario]:
        """Build Bull/Base/Bear scenarios from scores and forecasts."""
        scenarios = []

        # Base scenario: use 20D forecast if available
        fc_20 = forecasts.get(20)
        base_return = fc_20.expected_return_pct if (fc_20 and fc_20.status == "COMPUTED") else 0.0

        # Bull scenario
        bull_factors = []
        if score.fundamental_score > 65:
            bull_factors.append("أساسيات قوية")
        if score.valuation_label == "CHEAP":
            bull_factors.append("تقييم رخيص نسبياً")
        if score.trend_direction == "UP":
            bull_factors.append("اتجاه صاعد")
        scenarios.append(Scenario(
            label="BULL",
            probability=round(max(0.1, score.master_score / 200), 2),
            expected_return_pct=round((base_return or 0) * 1.8, 1),
            key_drivers=bull_factors or ["لا يوجد محفز واضح للسيناريو المتفائل"],
        ))

        # Base scenario
        base_factors = ["التوقع الأساسي للنموذج (منتصف الطريق)"]
        scenarios.append(Scenario(
            label="BASE",
            probability=round(max(0.4, 1 - abs(score.master_score - 50) / 100), 2),
            expected_return_pct=round(base_return or 0, 1),
            key_drivers=base_factors,
        ))

        # Bear scenario
        bear_factors = []
        if score.fundamental_score < 40:
            bear_factors.append("أساسيات ضعيفة")
        if score.macro_score < 40:
            bear_factors.append("ضغط الاقتصاد الكلي")
        if score.volatility_regime == "HIGH":
            bear_factors.append("تذبذب مرتفع")
        if score.liquidity_label == "ILLIQUID":
            bear_factors.append("سيولة منخفضة")
        scenarios.append(Scenario(
            label="BEAR",
            probability=round(max(0.1, (100 - score.master_score) / 200), 2),
            expected_return_pct=round((base_return or 0) * -1.5, 1),
            key_drivers=bear_factors or ["ضغط الاتجاه العام للسوق"],
        ))

        return scenarios

    def _find_best_horizon(self, forecasts: dict) -> Optional[int]:
        """Find horizon with highest confidence and probability_up."""
        best_h, best_val = None, -1.0
        for h, fc in forecasts.items():
            if fc.status == "COMPUTED" and fc.probability_up is not None:
                val = (fc.probability_up or 0.5) * (fc.confidence or 0)
                if val > best_val:
                    best_val = val
                    best_h = h
        return best_h

    def generate_report(self, ticker: str) -> CompanyReport:
        # Master score
        score = self.ranker.rank_ticker(ticker)

        # Multi-horizon forecasts
        forecasts = self.forecast_engine.forecast(ticker)
        forecast_dicts = {h: fc.to_dict() for h, fc in forecasts.items()}

        # Scenarios
        scenarios = self._build_scenarios(score, forecasts)
        best_horizon = self._find_best_horizon(forecasts)

        # Drivers narrative
        up_drivers = []
        down_risks = []

        if score.fundamental_score > 65:
            up_drivers.append(f"أساسيات قوية (درجة: {score.fundamental_score:.0f}/100)")
        if score.valuation_label == "CHEAP":
            up_drivers.append("التقييم رخيص نسبياً مقارنة بالقطاع")
        if score.is_valid_pullback:
            up_drivers.append("السهم في منطقة تراجع — سعر الدخول المقترح أقل من السعر الحالي ✅")
        if score.trend_direction == "UP":
            up_drivers.append("الاتجاه العام صاعد (فوق SMA20 و SMA50)")

        if score.macro_score < 40:
            down_risks.append(f"ضغط الاقتصاد الكلي: أسعار فائدة مرتفعة ({score.macro_score:.0f}/100)")
        if score.liquidity_label in ("LOW", "ILLIQUID"):
            down_risks.append(f"سيولة منخفضة ({score.liquidity_label}) — صعوبة الخروج")
        if score.volatility_regime in ("HIGH", "EXTREME"):
            down_risks.append(f"تذبذب {score.volatility_regime} — نطاق سعري واسع")
        if score.fundamental_score < 40:
            down_risks.append(f"أساسيات ضعيفة ({score.fundamental_score:.0f}/100)")
        if score.valuation_label == "EXPENSIVE":
            down_risks.append("التقييم مرتفع نسبياً مقارنة بالقطاع")

        # Why no trade
        why_no = []
        if not score.is_valid_pullback:
            why_no.append("لا تتوفر منطقة دخول Pullback (سعر الدخول يجب أن يكون أقل من السعر الحالي)")
        if score.liquidity_label == "ILLIQUID":
            why_no.append("سيولة غير كافية للتداول الآمن")

        report = CompanyReport(
            ticker=ticker,
            company_name=score.company_name,
            sector=score.sector,
            current_price=score.current_price,
            computed_at=score.computed_at,
            master_score=score.master_score,
            fundamental_score=score.fundamental_score,
            valuation_score=score.valuation_score,
            technical_score=score.technical_score,
            liquidity_score=score.liquidity_score,
            macro_score=score.macro_score,
            sector_score=score.sector_score,
            valuation_label=score.valuation_label,
            liquidity_label=score.liquidity_label,
            market_regime=score.market_regime,
            trend_direction=score.trend_direction,
            volatility_regime=score.volatility_regime,
            is_valid_pullback=score.is_valid_pullback,
            forecasts=forecast_dicts,
            best_horizon=best_horizon,
            scenarios=scenarios,
            up_drivers=up_drivers,
            down_risks=down_risks,
            why_no_trade=why_no,
            data_quality=score.data_quality,
            confidence=score.confidence,
            warnings=score.all_warnings,
        )
        return report


EGX_TICKERS = [
    "COMI.CA", "TMGH.CA", "SWDY.CA", "HRHO.CA", "FWRY.CA",
    "PHDC.CA", "ESRS.CA", "HELI.CA", "AMOC.CA", "ISPH.CA",
    "ETEL.CA", "ABUK.CA", "MFPC.CA",
]

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "COMI.CA"
    engine = CompanyIntelligenceEngine()

    print(f"\n{'='*70}")
    print(f"🏛️ GEN-26 V42 — COMPANY INTELLIGENCE REPORT")
    print(f"   {ticker} | DATA: YFinance PROXY | STATUS: EXPERIMENTAL")
    print(f"{'='*70}\n")

    report = engine.generate_report(ticker)

    print(f"Company:       {report.company_name}")
    print(f"Sector:        {report.sector}")
    print(f"Current Price: {report.current_price} EGP")
    print(f"Master Score:  {report.master_score:.1f}/100")
    print(f"  Fundamental: {report.fundamental_score:.1f}")
    print(f"  Valuation:   {report.valuation_score:.1f} ({report.valuation_label})")
    print(f"  Technical:   {report.technical_score:.1f}")
    print(f"  Liquidity:   {report.liquidity_score:.1f} ({report.liquidity_label})")
    print(f"  Sector:      {report.sector_score:.1f}")
    print(f"  Macro:       {report.macro_score:.1f}")
    print(f"Market Regime: {report.market_regime} | Trend: {report.trend_direction}")
    print(f"Valid Pullback: {'YES ✅' if report.is_valid_pullback else 'NO ❌'}")

    print(f"\n✅ UP DRIVERS:")
    for d in report.up_drivers: print(f"  + {d}")
    print(f"\n⚠️  DOWN RISKS:")
    for r in report.down_risks: print(f"  - {r}")

    print(f"\n📊 MULTI-HORIZON FORECASTS:")
    for h in HORIZONS:
        fc = report.forecasts.get(h, {})
        status = fc.get("status", "N/A")
        if status == "COMPUTED":
            pu = fc.get('probability_up')
            er = fc.get('expected_return_pct')
            lb = fc.get('price_range', {}).get('lower')
            ub = fc.get('price_range', {}).get('upper')
            print(f"  {h:>3}D: P(up)={pu:.0%}, ExpRet={er:+.1f}%, Range=[{lb:.2f}–{ub:.2f}], Conf={fc.get('confidence'):.0%}")
        else:
            print(f"  {h:>3}D: {status}")

    print(f"\n📈 SCENARIOS (60D outlook):")
    for s in report.scenarios:
        print(f"  {s.label:6}: P={s.probability:.0%}, ExpReturn={s.expected_return_pct:+.1f}%")
        for kd in s.key_drivers[:2]:
            print(f"         - {kd}")

    # Save
    out_path = os.path.join(os.path.dirname(_HERE), "reports", f"company_report_{ticker.replace('.','_')}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
    print(f"\n✅ Report saved: {out_path}")
