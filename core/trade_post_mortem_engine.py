#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/trade_post_mortem_engine.py — Forensic Trade Post-Mortem & Reflexion Engine
# Analyzes losing or degraded trades to diagnose root causes:
# - Bull Trap / Low Volume Breakout
# - Volatility Whipsaw & Tight Stop Hunting
# - Liquidity Exhaustion Reversal
# - Macro Regime Shift / Interest Rate Shock
# - Excessive Slippage & Market Impact Drag
# Outputs actionable verbal heuristics and structured machine negation filters.
# =============================================================================

import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import datetime
import uuid
import logging

logger = logging.getLogger("GEN26.TradePostMortemEngine")


@dataclass
class PostMortemReport:
    report_id: str
    ticker: str
    entry_price: float
    exit_price: float
    realized_pnl_pct: float
    holding_period_days: int
    failure_category: str
    diagnosis_ar: str
    culprit_factors: List[str]
    actionable_rule_ar: str
    actionable_code_filter: str
    quarantine_tag: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "ticker": self.ticker,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "realized_pnl_pct": self.realized_pnl_pct,
            "holding_period_days": self.holding_period_days,
            "failure_category": self.failure_category,
            "diagnosis_ar": self.diagnosis_ar,
            "culprit_factors": self.culprit_factors,
            "actionable_rule_ar": self.actionable_rule_ar,
            "actionable_code_filter": self.actionable_code_filter,
            "quarantine_tag": self.quarantine_tag,
            "timestamp": self.timestamp
        }


class TradePostMortemEngine:
    """
    Forensic engine implementing the Reflexion architecture for quantitative trading.
    Performs algorithmic root-cause analysis on unprofitable trades.
    """

    @classmethod
    def diagnose_trade(
        cls,
        ticker: str,
        entry_price: float,
        exit_price: float,
        entry_features: Dict[str, Any],
        exit_reason: str = "STOP_LOSS",
        holding_period_days: int = 5,
        slippage_pct: float = 0.15
    ) -> PostMortemReport:
        """
        Executes a diagnostic post-mortem on a closed trade.
        """
        pnl_pct = ((exit_price - entry_price) / max(entry_price, 1e-4)) * 100.0
        rep_id = f"PM_{ticker}_{uuid.uuid4().hex[:6].upper()}"

        vol_ratio = float(entry_features.get("volume_ratio", 1.0))
        cmf = float(entry_features.get("cmf", 0.05))
        mfi = float(entry_features.get("mfi", 50.0))
        adx = float(entry_features.get("adx", 25.0))
        regime_entry = str(entry_features.get("regime_at_entry", "BULL"))
        regime_exit = str(entry_features.get("regime_at_exit", regime_entry))
        spread_pct = float(entry_features.get("spread_pct", 0.30))

        culprits = []

        # Category 1: Bull Trap on low volume / negative money flow
        if vol_ratio < 0.80 and cmf < 0.0:
            category = "BULL_TRAP_LOW_VOLUME"
            culprits.extend(["volume_ratio", "cmf"])
            diagnosis = (
                f"فشل كسر صاعد لسهم {ticker}: تم الدخول رغم انخفاض حجم التداول "
                f"(حجم نسبي {vol_ratio:.2f}) مع تدفق سيولة شايكين سالب (CMF={cmf:.2f})، "
                f"مما يثبت غياب المشتري المؤسسي وحدوث مصيدة سيولة."
            )
            rule_ar = (
                f"حظر الشراء عند كسر القمم لسهم {ticker} إذا كان الحجم أقل من 80% "
                f"من متوسط 20 يوماً مع CMF سالب."
            )
            code_filter = f"vol_ratio >= 0.80 and cmf >= 0.0"
            quarantine = f"quarantine_low_vol_breakout_{ticker.lower()}"

        # Category 2: Exhaustion Reversal (Bought at extreme top)
        elif mfi > 78.0 or entry_features.get("gap_type") == "EXHAUSTION":
            category = "EXHAUSTION_REVERSAL"
            culprits.extend(["mfi", "gap_type"])
            diagnosis = (
                f"انعكاس إنهاك شرائي لسهم {ticker}: تم الدخول في منطقة تشبع شرائي حاد "
                f"(MFI={mfi:.1f}) بالقرب من فجوة إنهاك، مما أدى إلى تصحيح سريع ضد المركز."
            )
            rule_ar = f"منع الدخول الطويل في {ticker} إذا تجاوز مؤشر MFI مستوى 78."
            code_filter = f"mfi <= 78.0"
            quarantine = f"quarantine_exhaustion_top_{ticker.lower()}"

        # Category 3: Macro Regime Shift during trade life
        elif regime_entry != regime_exit and "CRISIS" in regime_exit:
            category = "MACRO_REGIME_SHOCK"
            culprits.extend(["macro_regime_transition"])
            diagnosis = (
                f"صدمة نظام كلي: تحول نظام السوق أثناء الاحتفاظ من {regime_entry} إلى {regime_exit}، "
                f"مما دمر الأفضلية الإحصائية الموضعية."
            )
            rule_ar = "تفعيل الخروج الفوري وإلغاء أوامر الشراء عند تحول النظام إلى نظام أزمة أو تذبذب مرتفع."
            code_filter = f"regime != 'CRISIS_HIGH_VOL'"
            quarantine = "quarantine_crisis_regime_longs"

        # Category 4: Excessive Slippage & Spread Drag
        elif slippage_pct > 0.40 or spread_pct > 1.2:
            category = "EXCESSIVE_SLIPPAGE_DRAG"
            culprits.extend(["slippage_pct", "spread_pct"])
            diagnosis = (
                f"تآكل الربحية بفعل الانزلاق والفروق السعرية: الفارق السعري ({spread_pct:.2f}%) "
                f"والانزلاق ({slippage_pct:.2f}%) استهلكا أكثر من 50% من الهامش المتوقع."
            )
            rule_ar = f"حظر تنفيذ أوامر السوق على {ticker} إذا تجاوز الفارق السعري (Spread) 1.0%."
            code_filter = f"spread_pct <= 1.00"
            quarantine = f"quarantine_wide_spread_{ticker.lower()}"

        # Category 5: Volatility Whipsaw / Tight Stop Loss
        else:
            category = "VOLATILITY_WHIPSAW"
            culprits.extend(["atr_stop_distance", "adx"])
            diagnosis = (
                f"ذبذبة عشوائية وضرب وقف خسارة ضيق: وقف الخسارة كان داخل نطاق الذبذبة الطبيعية (ATR) "
                f"في ظل اتجاه ضعيف (ADX={adx:.1f})."
            )
            rule_ar = f"مضاعفة المسافة الدنيا لوقف الخسارة إلى 1.5 * ATR في بيئات الاتجاه الضعيف (ADX < 20)."
            code_filter = f"stop_distance >= (1.5 * atr)"
            quarantine = f"quarantine_tight_stop_{ticker.lower()}"

        logger.info(
            "Post-Mortem completed for %s [%s]: Realized PnL=%.2f%%, Category=%s",
            ticker, rep_id, pnl_pct, category
        )

        # Automatically enforce 48-hour cooling-off lock if trade hit stop loss or lost capital
        if "STOP" in exit_reason.upper() or pnl_pct < 0:
            cls.register_stop_loss_hit(ticker=ticker, reason=diagnosis, lock_hours=48)

        return PostMortemReport(
            report_id=rep_id,
            ticker=ticker,
            entry_price=round(entry_price, 2),
            exit_price=round(exit_price, 2),
            realized_pnl_pct=round(pnl_pct, 2),
            holding_period_days=holding_period_days,
            failure_category=category,
            diagnosis_ar=diagnosis,
            culprit_factors=culprits,
            actionable_rule_ar=rule_ar,
            actionable_code_filter=code_filter,
            quarantine_tag=quarantine
        )

    # =========================================================================
    # EPISODIC FAILURE MEMORY: 48-HOUR COOLING-OFF LOCK (ANTI-REVENGE TRADING)
    # =========================================================================

    COOLING_OFF_FILE = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "cooling_off_registry.json"
    )

    @classmethod
    def _load_cooling_off_store(cls) -> Dict[str, Any]:
        if os.path.exists(cls.COOLING_OFF_FILE):
            try:
                with open(cls.COOLING_OFF_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    @classmethod
    def _save_cooling_off_store(cls, data: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(cls.COOLING_OFF_FILE), exist_ok=True)
        try:
            with open(cls.COOLING_OFF_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning("Failed to save cooling off registry: %s", e)

    @classmethod
    def register_stop_loss_hit(
        cls,
        ticker: str,
        reason: str = "",
        lock_hours: int = 48
    ) -> Dict[str, Any]:
        """
        Registers an emergency 48-hour trading ban on a ticker after a stop-loss is hit.
        Eliminates revenge trading and emotional capital churn.
        """
        sym = ticker.upper().strip()
        now = datetime.datetime.now()
        expires = now + datetime.timedelta(hours=lock_hours)

        store = cls._load_cooling_off_store()
        record = {
            "ticker": sym,
            "locked_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "expires_at": expires.strftime("%Y-%m-%d %H:%M:%S"),
            "lock_hours": lock_hours,
            "reason_ar": reason or "ضرب وقف الخسارة — تفعيل حظر التداول الإلزامي 48 ساعة لمكافحة التداول الانتقامي.",
            "is_active": True
        }
        store[sym] = record
        cls._save_cooling_off_store(store)
        logger.warning(
            "🚨 Cooling-off period enforced for %s for %d hours until %s",
            sym, lock_hours, record["expires_at"]
        )
        return record

    @classmethod
    def is_ticker_in_cooling_off(cls, ticker: str) -> Tuple[bool, float, str]:
        """
        Checks whether a ticker is currently subject to the 48-hour cooling-off lock.
        Returns: (is_locked: bool, remaining_hours: float, reason_ar: str)
        """
        sym = ticker.upper().strip()
        store = cls._load_cooling_off_store()
        rec = store.get(sym)
        if not rec:
            return False, 0.0, ""

        try:
            expires_dt = datetime.datetime.strptime(rec["expires_at"], "%Y-%m-%d %H:%M:%S")
            now = datetime.datetime.now()
            if now < expires_dt:
                rem_hours = round((expires_dt - now).total_seconds() / 3600.0, 1)
                return True, rem_hours, rec.get("reason_ar", "حظر تداول إلزامي")
            else:
                # Expired -> clear lock
                del store[sym]
                cls._save_cooling_off_store(store)
                return False, 0.0, ""
        except Exception:
            return False, 0.0, ""

    @classmethod
    def clear_cooling_off(cls, ticker: str) -> bool:
        """Manually lifts the cooling-off lock for a specific ticker."""
        sym = ticker.upper().strip()
        store = cls._load_cooling_off_store()
        if sym in store:
            del store[sym]
            cls._save_cooling_off_store(store)
            return True
        return False

    @classmethod
    def get_all_active_locks(cls) -> List[Dict[str, Any]]:
        """Returns all currently active cooling-off locks."""
        store = cls._load_cooling_off_store()
        now = datetime.datetime.now()
        active = []
        for sym, rec in list(store.items()):
            try:
                exp = datetime.datetime.strptime(rec["expires_at"], "%Y-%m-%d %H:%M:%S")
                if now < exp:
                    rec_copy = dict(rec)
                    rec_copy["remaining_hours"] = round((exp - now).total_seconds() / 3600.0, 1)
                    active.append(rec_copy)
            except Exception:
                pass
        return active
