# 08. Episodic Failure Memory & Negative Feedback Engine

## 1. Executive Summary
The **Episodic Failure Memory Engine** (`core/failure_memory.py`) prevents the quant system from repeating unprofitable setups. Whenever a stop-loss is triggered or an algorithmic strategy fails out-of-sample, a comprehensive post-mortem root-cause analysis is conducted, storing the failure signature in SQLite and enforcing active quarantine rules.

---

## 2. Failure Memory Record Structure

```json
{
  "failure_id": "FAIL_20260815_COMI_01",
  "timestamp": "2026-08-15T14:30:00",
  "ticker": "COMI.CA",
  "strategy_name": "Momentum Breakout High Volatility",
  "market_regime": "HIGH_RATES_STABLE_FX",
  "loss_amount_egp": 3450.00,
  "loss_pct": 7.20,
  "root_cause_analysis": "Entry occurred at upper Bollinger Band resistance during low volume lunch session prior to CBE rate decision announcement.",
  "lessons_learned_ar": "حظر الدخول في اختراقات الزخم في فترات انخفاض السيولة قبل اجتماعات لجنة السياسة النقدية بالبنك المركزي.",
  "quarantine_rule": "BLOCK_BREAKOUT_ON_CBE_MEETING_DAYS",
  "active_quarantine": 1
}
```

---

## 3. Quarantine & Active Filtering Protocol

Before any trade order is approved:
1. The **Risk Agent** queries `failure_cases_memory` for matching pattern signatures:
   - Identical Ticker + Identical Indicator Overbought State + Low Volume.
2. If an active quarantine rule matches the candidate setup:
   - Conviction penalty: $-40.0$ points.
   - Rejection advisory: *"تم رفض الصفقة تلقائياً لوجود سابقة فشل مماثلة مسجلة في الذاكرة التراكمية (Quarantined Failure Pattern)."*

---

## 4. Periodic Review & Memory Pruning

- **Quarantine Expiration**: Quarantines undergo automated re-evaluation after 60 trading days.
- **Statistical Significance**: A quarantine rule is permanently codified if historical recurrence produces $< 30\%$ win rate across 10 simulation folds.
