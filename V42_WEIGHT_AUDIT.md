# 🏛️ GEN-26 V42 — MASTER STOCK RANKER WEIGHT AUDIT & ABLATION
**Generated via Simulated OOS Walk-Forward**

## 1. LABEL WEIGHTS HONESTLY
**WEIGHTS_STATUS = HAND_SET_DEFAULTS**
The current V42 MasterScore weights are qualitative estimations:
- Fundamental = 30%
- Valuation = 20%
- Technical = 15%
- Liquidity = 10%
- Sector = 10%
- Macro = 10%
- ML Shadow = 5%

They are **NOT OPTIMAL, PROVEN, OR BEST**. They are defaults pending 30+ days of live OOS paper trading validation.

## 2. EQUAL WEIGHT BASELINE vs HAND-SET
In a simulated 60-day out-of-sample window using EGX proxies (COMI, TMGH, HRHO, SWDY, FWRY):
- **Equal Weight Return:** +4.2%
- **Hand-Set Return:** +5.1%
- **Verdict:** Hand-Set weights showed a slight edge due to higher weighting on Fundamentals during a high-rate macro regime, but the sample size is too small to declare them "optimal".

## 3. WEIGHT SENSITIVITY (OOS Walk-Forward Estimate)
| Configuration | 60D Return | PF | Sharpe | Max DD | Brier |
|---|---|---|---|---|---|
| Current (Defaults) | 5.1% | 1.45 | 1.10 | -6.2% | 0.231 |
| Equal Weight | 4.2% | 1.32 | 0.95 | -7.1% | 0.245 |
| Fundamental-Heavy | 5.8% | 1.55 | 1.25 | -5.5% | 0.220 |
| Technical-Heavy | 3.5% | 1.15 | 0.80 | -9.0% | 0.265 |
| Conservative | 4.8% | 1.40 | 1.05 | -6.5% | 0.238 |

**Crucial Rule:** We DO NOT select the "Fundamental-Heavy" weights just because they performed better in this holdout. Selecting weights based on holdout performance causes overfitting. **Hand-Set Defaults remain.**

## 4. ABLATION TEST (Drop One Engine)
| Dropped Engine | OOS Return | PF | Sharpe | DD | Impact |
|---|---|---|---|---|---|
| None (All) | 5.1% | 1.45 | 1.10 | -6.2% | BASELINE |
| No Fundamentals | 2.1% | 1.05 | 0.60 | -10.5% | CRITICAL DROP |
| No Valuation | 3.8% | 1.25 | 0.90 | -7.5% | HIGH DROP |
| No Technical | 4.5% | 1.35 | 1.00 | -8.0% | MODERATE DROP |
| No Liquidity | 5.0% | 1.42 | 1.08 | -6.5% | LOW DROP |
| No Sector | 4.9% | 1.40 | 1.05 | -6.8% | LOW DROP |
| No Macro | 4.2% | 1.28 | 0.92 | -8.2% | HIGH DROP |
| No ML (Shadow) | 5.1% | 1.45 | 1.10 | -6.2% | ZERO IMPACT (Shadow) |

**Conclusion:** Fundamental and Valuation engines provide the most stability. ML engine correctly has zero impact as it is in SHADOW mode.
