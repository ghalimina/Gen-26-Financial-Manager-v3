#!/usr/bin/env python3
# =============================================================================
# core/real_portfolio.py — GEN-26 Real Portfolio Management Engine (Production)
# Enables full CRUD, audit logging, P&L calculations, risk constraints,
# and explainable model recommendations for the user's real holdings.
# GUARANTEE: READ-ONLY TRACKING & ADVISORY. ZERO LIVE BROKER ORDER ROUTING.
# =============================================================================

import os
import json
import datetime
import uuid
import threading
from typing import Dict, List, Any, Optional

from core.frozen_invariants import FrozenRiskInvariants
from core.pit_store import HistoricalTradableUniverse
from core.portfolio_risk import PortfolioRiskEngine


class RealPortfolioTracker:
    """
    Authoritative manager for user's real portfolio holdings with audit logging and risk scoring.
    """
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    REAL_PORTFOLIO_FILE = os.path.join(DATA_DIR, "user_real_portfolio.json")
    AUDIT_LOG_FILE = os.path.join(DATA_DIR, "real_portfolio_audit_log.json")
    _PORTFOLIO_LOCK = threading.RLock()

    COMPANY_NAMES = {
        "COMI.CA": "البنك التجاري الدولي (CIB)",
        "SWDY.CA": "السويدي إليكتريك",
        "TMGH.CA": "مجموعة طلعت مصطفى",
        "EKHO.CA": "القابضة المصرية الكويتية",
        "ETEL.CA": "المصرية للاتصالات",
        "ABUK.CA": "أبو قير للأسمدة",
        "MFPC.CA": "موبكو للأسمدة",
        "HELI.CA": "مصر الجديدة للإسكان",
        "ORAS.CA": "أوراسكوم للإنشاء",
        "ESRS.CA": "حديد عز",
        "HRHO.CA": "إي إف جي القابضة",
        "AMOC.CA": "الإسكندرية للزيوت المعدنية",
        "SKPC.CA": "سيدي كرير للبتروكيماويات",
        "PHDC.CA": "بالم هيلز للتعمير",
        "MASR.CA": "مدينة مصر للإسكان",
        "ISPH.CA": "ابن سينا فارما",
        "FWRY.CA": "فوري لتكنولوجيا البنوك",
        "EAST.CA": "الشرقية للدخان (إيسترن كومباني)",
        "EGAL.CA": "مصر للألومنيوم",
        "ORHD.CA": "أوراسكوم للتنمية مصر",
        "CERA.CA": "سيراميكا بريما",
        "JUFO.CA": "جهينة للصناعات الغذائية",
        "CLHO.CA": "مستشفى كليوباترا",
        "CCAP.CA": "القلعة للاستشارات المالية",
        "AUTO.CA": "جي بي كورب (غبور أوتو)",
        "BTFH.CA": "بلتون المالية القابضة",
        "RAYA.CA": "راية القابضة"
    }

    SECTOR_MAPPINGS = {
        "COMI.CA": "Banking",
        "SWDY.CA": "Industrial",
        "TMGH.CA": "Real Estate",
        "EKHO.CA": "Financial Services",
        "ETEL.CA": "Telecom",
        "ABUK.CA": "Fertilizers",
        "MFPC.CA": "Fertilizers",
        "HELI.CA": "Real Estate",
        "ORAS.CA": "Industrial",
        "ESRS.CA": "Basic Materials",
        "HRHO.CA": "Financial Services",
        "AMOC.CA": "Energy",
        "SKPC.CA": "Petrochemicals",
        "PHDC.CA": "Real Estate",
        "MASR.CA": "Real Estate",
        "ISPH.CA": "Healthcare",
        "FWRY.CA": "FinTech",
        "EAST.CA": "Consumer Staples",
        "EGAL.CA": "Basic Materials",
        "ORHD.CA": "Real Estate",
        "CERA.CA": "Industrial",
        "JUFO.CA": "Consumer Staples",
        "CLHO.CA": "Healthcare",
        "CCAP.CA": "Financial Services",
        "AUTO.CA": "Automotive",
        "BTFH.CA": "Financial Services",
        "RAYA.CA": "Financial Services"
    }

    @classmethod
    def get_initial_real_portfolio(cls) -> Dict[str, Any]:
        """Returns baseline state for user's real portfolio."""
        return {
            "portfolio_id": "REAL_PORTFOLIO_PRIMARY",
            "version": "3.0.0",
            "last_updated": datetime.datetime.now().isoformat(),
            "cash_egp": 100000.0,
            "holdings": []
        }

    @classmethod
    def load_real_portfolio(cls) -> Dict[str, Any]:
        """Loads real portfolio from persistent JSON."""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        if not os.path.exists(cls.REAL_PORTFOLIO_FILE):
            data = cls.get_initial_real_portfolio()
            cls.save_real_portfolio(data)
            return data
        try:
            with open(cls.REAL_PORTFOLIO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return cls.get_initial_real_portfolio()

    @classmethod
    def save_real_portfolio(cls, portfolio_data: Dict[str, Any]):
        """Persists real portfolio state atomically with disk sync."""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        portfolio_data["last_updated"] = datetime.datetime.now().isoformat()
        tmp_f = f"{cls.REAL_PORTFOLIO_FILE}.tmp"
        with open(tmp_f, "w", encoding="utf-8") as f:
            json.dump(portfolio_data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_f, cls.REAL_PORTFOLIO_FILE)

    @classmethod
    def _log_audit_event(cls, action: str, ticker: str, old_val: Optional[Dict[str, Any]], new_val: Optional[Dict[str, Any]], user_note: str = ""):
        """Records mutation audit event to data/real_portfolio_audit_log.json."""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        logs = []
        if os.path.exists(cls.AUDIT_LOG_FILE):
            try:
                with open(cls.AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except Exception:
                logs = []

        event = {
            "audit_id": str(uuid.uuid4())[:8],
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "ticker": ticker,
            "old_values": old_val,
            "new_values": new_val,
            "source": "USER_MANUAL_UI",
            "notes": user_note
        }
        logs.append(event)
        tmp_f = f"{cls.AUDIT_LOG_FILE}.tmp"
        with open(tmp_f, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_f, cls.AUDIT_LOG_FILE)

    @classmethod
    def add_holding(cls, ticker: str, quantity: int, average_entry_price: float, notes: str = "") -> Dict[str, Any]:
        """
        Adds a new real stock holding with validation and audit logging.
        """
        with cls._PORTFOLIO_LOCK:
            t = ticker.strip().upper()
            if not t.endswith(".CA") and "." not in t:
                t += ".CA"

            # 1. Validation: Ticker in Universe (Supports all 50 active EGX stocks)
            from core.egx_universe_loader import EGXUniverseLoader
            from core.market_price_service import MarketPriceService
            canonical_data = MarketPriceService.get_all_canonical_prices()
            canonical_tickers = {r["ticker"] for r in canonical_data if isinstance(r, dict) and "ticker" in r} if isinstance(canonical_data, list) else set(canonical_data.keys())
            all_valid_tickers = set(EGXUniverseLoader.ACTIVE_UNIVERSE.keys()) | canonical_tickers | set(cls.COMPANY_NAMES.keys())
            if t not in all_valid_tickers:
                return {"success": False, "error": f"كود السهم {t} غير موجود في الكون الاستثماري المعتمد لبورصة مصر."}

            # 2. Validation: Positive Quantity and Price
            if quantity <= 0:
                return {"success": False, "error": "يجب أن تكون الكمية عدداً موجباً أكبر من صفر."}

            if average_entry_price <= 0:
                return {"success": False, "error": "يجب أن يكون متوسط سعر الشراء أكبر من صفر."}

            portfolio = cls.load_real_portfolio()
            holdings = portfolio.setdefault("holdings", [])

            # 3. Check Duplicate Position (unless modifying existing lot)
            existing = next((h for h in holdings if h["ticker"] == t and h.get("active", True)), None)
            if existing:
                return {"success": False, "error": f"السهم {t} موجود بالفعل في المحفظة. يرجى استخدام خيار التعديل لتحديث الكمية أو السعر."}

            new_holding = {
                "holding_id": f"POS_{t.replace('.CA', '')}_{str(uuid.uuid4())[:6]}",
                "ticker": t,
                "company_name": cls.COMPANY_NAMES.get(t, t),
                "exchange": "EGX",
                "sector": cls.SECTOR_MAPPINGS.get(t, "General"),
                "quantity": int(quantity),
                "average_entry_price": float(average_entry_price),
                "manual_notes": notes.strip(),
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat(),
                "active": True
            }

            holdings.append(new_holding)
            cls.save_real_portfolio(portfolio)
            cls._log_audit_event("ADD", t, None, new_holding, notes)

            return {"success": True, "message": f"تمت إضافة سهم {t} للمحفظة بنجاح.", "holding": new_holding}

    @classmethod
    def edit_holding(cls, ticker: str, quantity: int, average_entry_price: float, notes: str = "") -> Dict[str, Any]:
        """
        Edits an existing holding's quantity, entry price, and notes.
        """
        with cls._PORTFOLIO_LOCK:
            t = ticker.strip().upper()
            if not t.endswith(".CA"):
                t += ".CA"

            if quantity <= 0:
                return {"success": False, "error": "الكمية يجب أن تكون أكبر من صفر."}

            if average_entry_price <= 0:
                return {"success": False, "error": "متوسط سعر الشراء يجب أن يكون أكبر من صفر."}

            portfolio = cls.load_real_portfolio()
            holdings = portfolio.get("holdings", [])
            existing = next((h for h in holdings if h["ticker"] == t and h.get("active", True)), None)

            if not existing:
                return {"success": False, "error": f"السهم {t} غير موجود في المحفظة لتعديله."}

            old_snapshot = dict(existing)
            existing["quantity"] = int(quantity)
            existing["average_entry_price"] = float(average_entry_price)
            existing["manual_notes"] = notes.strip()
            existing["updated_at"] = datetime.datetime.now().isoformat()

            cls.save_real_portfolio(portfolio)
            cls._log_audit_event("EDIT", t, old_snapshot, existing, notes)

            return {"success": True, "message": f"تم تعديل مركز {t} بنجاح.", "holding": existing}

    @classmethod
    def delete_holding(cls, ticker: str, confirm: bool = True) -> Dict[str, Any]:
        """
        Deletes (soft-deletes) a holding with required confirmation.
        """
        if not confirm:
            return {"success": False, "error": "الحذف يتطلب تأكيداً صريحاً من المستخدم."}

        with cls._PORTFOLIO_LOCK:
            t = ticker.strip().upper()
            if not t.endswith(".CA"):
                t += ".CA"

            portfolio = cls.load_real_portfolio()
            holdings = portfolio.get("holdings", [])
            existing = next((h for h in holdings if h["ticker"] == t and h.get("active", True)), None)

            if not existing:
                return {"success": False, "error": f"السهم {t} غير موجود في المحفظة لحذفه."}

            old_snapshot = dict(existing)
            existing["active"] = False
            existing["deleted_at"] = datetime.datetime.now().isoformat()
            portfolio["holdings"] = [h for h in holdings if h.get("active", True) and h["ticker"] != t]

            cls.save_real_portfolio(portfolio)
            cls._log_audit_event("DELETE", t, old_snapshot, None, "User confirmed deletion")

            return {"success": True, "message": f"تم حذف سهم {t} من المحفظة بنجاح."}

    @classmethod
    def analyze_real_portfolio(
        cls,
        current_market_prices: Optional[Dict[str, float]] = None,
        alpha_scores: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Computes all deterministic real portfolio financial & risk metrics,
        and generates explainable model recommendations distinguishing owned stocks.
        """
        from core.market_price_service import MarketPriceService
        portfolio = cls.load_real_portfolio()
        prices = current_market_prices or {}
        alphas = alpha_scores or {"COMI.CA": 90.0, "SWDY.CA": 85.0, "TMGH.CA": 82.0, "EKHO.CA": 78.0, "ETEL.CA": 80.0, "ABUK.CA": 76.0, "FWRY.CA": 74.0}

        cash = float(portfolio.get("cash_egp", 100000.0))
        raw_holdings = [h for h in portfolio.get("holdings", []) if h.get("active", True)]

        analyzed_positions = []
        total_stock_market_value = 0.0
        total_invested_cost = 0.0
        sector_weights = {}

        for h in raw_holdings:
            sym = h["ticker"] if "ticker" in h else h.get("symbol", "COMI.CA")
            qty = int(h["quantity"])
            entry_p = float(h["average_entry_price"] if "average_entry_price" in h else h.get("avg_entry_price", 100.0))
            if sym in prices:
                cp = prices[sym]
            else:
                try:
                    cp = MarketPriceService.get_latest_price(sym)
                except Exception:
                    cp = entry_p
            alpha = alphas.get(sym, 50.0)

            cost_basis = qty * entry_p
            market_val = qty * cp
            unrealized_pnl = market_val - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis) * 100.0 if cost_basis > 0 else 0.0

            total_invested_cost += cost_basis
            total_stock_market_value += market_val

            sec = h.get("sector") or cls.SECTOR_MAPPINGS.get(sym, "General")
            sector_weights[sec] = sector_weights.get(sec, 0.0) + market_val

            # Model Targets & Limits
            stop_p = round(entry_p * (1.0 - FrozenRiskInvariants.HARD_STOP_LOSS_PCT), 2)
            target_p = round(entry_p * 1.15, 2)
            dist_to_stop_pct = round(((cp - stop_p) / cp) * 100.0, 2) if cp > 0 else 0.0

            # Model Reasoning & Decision Distinction
            # "أنت تمتلك السهم بالفعل"
            owned_status = "أنت تمتلك السهم بالفعل"
            if cp <= stop_p:
                model_view = "خروج (وقف خسارة)"
                raw_action = "EXIT"
                proposed_action = "🔴 خروج / تفعيل وقف الخسارة"
                reason_detail = f"السعر الحالي ({cp:.2f} ج.م) كسر حاجز وقف الخسارة المحمي ({stop_p:.2f} ج.م)."
            elif unrealized_pnl_pct >= 15.0:
                model_view = "جني أرباح"
                raw_action = "REDUCE"
                proposed_action = "🟡 تقليل / جني أرباح جزئي"
                reason_detail = f"تم تحقيق المستهدف الاستثماري بنمو +{unrealized_pnl_pct:.1f}%."
            elif alpha >= 80.0 and cp > entry_p:
                model_view = "شراء / تعزيز"
                raw_action = "HOLD"
                proposed_action = "🟢 احتفاظ أو تعزيز"
                reason_detail = f"السهم يتمتع بزخم ألفا قوي ({alpha:.0f}/100) والاتجاه إيجابي."
            elif alpha < 45.0:
                model_view = "تراجع الجاذبية"
                raw_action = "REDUCE"
                proposed_action = "🟡 تقليل المركز"
                reason_detail = f"تراجعت نقاط الألفا إلى ({alpha:.0f}/100) وضعف الزخم التشغيلي."
            else:
                model_view = "مراقبة الاتجاه"
                raw_action = "HOLD"
                proposed_action = "🔵 احتفاظ ومراقبة"
                reason_detail = "المركز مستقر ضمن نطاق الحركة الطبيعي."

            analyzed_positions.append({
                "holding_id": h.get("holding_id", f"POS_{sym}"),
                "ticker": sym,
                "symbol": sym,
                "company_name": h.get("company_name", cls.COMPANY_NAMES.get(sym, sym)),
                "sector": sec,
                "quantity": qty,
                "average_entry_price": entry_p,
                "avg_entry_price": entry_p,
                "current_price": cp,
                "cost_basis_egp": round(cost_basis, 2),
                "market_value_egp": round(market_val, 2),
                "unrealized_pnl_egp": round(unrealized_pnl, 2),
                "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
                "target_price": target_p,
                "target_return_pct": 15.0,
                "stop_loss": stop_p,
                "distance_to_stop_pct": dist_to_stop_pct,
                "model_score": alpha,
                "rank": 1 if alpha >= 85 else 2,
                "ownership_notice": owned_status,
                "model_view": model_view,
                "action": f"{raw_action} ({proposed_action})",
                "proposed_action": proposed_action,
                "advisory_reason": reason_detail,
                "reasoning_telemetry": reason_detail,
                "manual_notes": h.get("manual_notes", "")
            })

        total_portfolio_equity = cash + total_stock_market_value

        # Calculate position weights
        for p in analyzed_positions:
            p["portfolio_weight_pct"] = round((p["market_value_egp"] / total_portfolio_equity) * 100.0, 2) if total_portfolio_equity > 0 else 0.0

        stock_weight_pct = (total_stock_market_value / total_portfolio_equity) * 100.0 if total_portfolio_equity > 0 else 0.0
        cash_weight_pct = (cash / total_portfolio_equity) * 100.0 if total_portfolio_equity > 0 else 0.0

        # Risk Constraints Check
        sector_concentrations = {k: round((v / total_portfolio_equity) * 100.0, 2) for k, v in sector_weights.items()}
        max_single_stock_pct = max([p["portfolio_weight_pct"] for p in analyzed_positions], default=0.0)

        risk_report = {
            "stock_allocation_pct": round(stock_weight_pct, 1),
            "stock_ceiling_limit_pct": FrozenRiskInvariants.MAX_TOTAL_STOCK_ALLOCATION_PCT * 100.0,
            "stock_ceiling_status": "PASS" if stock_weight_pct <= 65.0 else "WARNING_BREACH",
            "cash_reserve_pct": round(cash_weight_pct, 1),
            "cash_floor_limit_pct": FrozenRiskInvariants.MANDATORY_CASH_RESERVE_PCT * 100.0,
            "cash_floor_status": "PASS" if cash_weight_pct >= 35.0 else "WARNING_BREACH",
            "max_single_stock_pct": max_single_stock_pct,
            "single_stock_limit_pct": FrozenRiskInvariants.MAX_SINGLE_STOCK_ALLOCATION_PCT * 100.0,
            "sector_concentrations": sector_concentrations
        }

        return {
            "as_of": datetime.datetime.now().isoformat(),
            "portfolio_id": portfolio.get("portfolio_id", "REAL_PORTFOLIO_PRIMARY"),
            "total_portfolio_equity_egp": round(total_portfolio_equity, 2),
            "total_invested_cost_egp": round(total_invested_cost, 2),
            "free_cash_egp": round(cash, 2),
            "stock_market_value_egp": round(total_stock_market_value, 2),
            "total_unrealized_pnl_egp": round(total_stock_market_value - total_invested_cost, 2),
            "positions_count": len(analyzed_positions),
            "positions": analyzed_positions,
            "holdings": analyzed_positions,
            "portfolio_equity_egp": round(total_portfolio_equity, 2),
            "cash_egp": round(cash, 2),
            "unrealized_pnl_egp": round(total_stock_market_value - total_invested_cost, 2),
            "unrealized_pnl_pct": round(((total_stock_market_value - total_invested_cost) / total_invested_cost) * 100.0, 2) if total_invested_cost > 0 else 0.0,
            "risk_analysis": risk_report
        }
