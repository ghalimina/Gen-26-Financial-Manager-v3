#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/portfolio_journal.py — GEN-26 Portfolio Journal & FIFO Performance Engine
# =============================================================================

import os
import json
import uuid
import datetime
from typing import Dict, List, Any, Optional

DEFAULT_JOURNAL_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "portfolio_journal_transactions.json")


def load_transactions(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    target = file_path or DEFAULT_JOURNAL_FILE
    if os.path.exists(target):
        try:
            with open(target, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_transactions(transactions: List[Dict[str, Any]], file_path: Optional[str] = None) -> None:
    target = file_path or DEFAULT_JOURNAL_FILE
    os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        json.dump(transactions, f, ensure_ascii=False, indent=2)


def add_transaction(
    ticker: str,
    action: str,
    quantity: int,
    price: float,
    date: Optional[str] = None,
    source: str = "MANUAL",
    decision_id: Optional[str] = None,
    notes: str = "",
    file_path: Optional[str] = None
) -> Dict[str, Any]:
    txs = load_transactions(file_path)
    sym = ticker.upper().strip()
    if not sym.endswith(".CA") and "." not in sym:
        sym = f"{sym}.CA"

    tx = {
        "transaction_id": str(uuid.uuid4())[:8],
        "ticker": sym,
        "action": action.upper().strip(),
        "quantity": int(quantity),
        "price": float(price),
        "date": date or datetime.date.today().isoformat(),
        "source": source,
        "decision_id": decision_id,
        "notes": notes,
        "created_at": datetime.datetime.now().isoformat()
    }
    txs.append(tx)
    save_transactions(txs, file_path)
    return tx


def update_transaction(
    transaction_id: str,
    quantity: Optional[int] = None,
    price: Optional[float] = None,
    notes: Optional[str] = None,
    file_path: Optional[str] = None
) -> bool:
    txs = load_transactions(file_path)
    for t in txs:
        if t.get("transaction_id") == transaction_id:
            if quantity is not None:
                t["quantity"] = int(quantity)
            if price is not None:
                t["price"] = float(price)
            if notes is not None:
                t["notes"] = notes
            t["updated_at"] = datetime.datetime.now().isoformat()
            save_transactions(txs, file_path)
            return True
    return False


def delete_transaction(transaction_id: str, file_path: Optional[str] = None) -> bool:
    txs = load_transactions(file_path)
    new_txs = [t for t in txs if t.get("transaction_id") != transaction_id]
    if len(new_txs) != len(txs):
        save_transactions(new_txs, file_path)
        return True
    return False


def compute_portfolio_performance(
    transactions: List[Dict[str, Any]],
    live_quotes: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    quotes = live_quotes or {}
    lots: Dict[str, List[Dict[str, Any]]] = {}
    closed_trades: List[Dict[str, Any]] = []

    for tx in transactions:
        sym = tx["ticker"]
        act = tx["action"]
        qty = tx["quantity"]
        px = tx["price"]

        if sym not in lots:
            lots[sym] = []

        if act == "BUY":
            lots[sym].append({"quantity": qty, "price": px, "date": tx.get("date")})
        elif act == "SELL":
            qty_to_sell = qty
            while qty_to_sell > 0 and lots[sym]:
                lot = lots[sym][0]
                matched_qty = min(lot["quantity"], qty_to_sell)
                cost = matched_qty * lot["price"]
                proceeds = matched_qty * px
                pnl = proceeds - cost
                closed_trades.append({
                    "ticker": sym,
                    "quantity": matched_qty,
                    "buy_price": lot["price"],
                    "sell_price": px,
                    "realized_pnl": pnl,
                    "pnl_pct": (pnl / cost) * 100.0 if cost > 0 else 0.0
                })
                lot["quantity"] -= matched_qty
                qty_to_sell -= matched_qty
                if lot["quantity"] <= 0:
                    lots[sym].pop(0)

    open_positions = []
    total_cost_basis = 0.0
    total_market_value = 0.0
    total_unrealized_pnl = 0.0

    for sym, open_lots in lots.items():
        total_qty = sum(l["quantity"] for l in open_lots)
        if total_qty > 0:
            cost = sum(l["quantity"] * l["price"] for l in open_lots)
            avg_cost = round(cost / total_qty, 2)
            cp = quotes.get(sym, avg_cost)
            mv = round(total_qty * cp, 2)
            unrealized = round(mv - cost, 2)
            unrealized_pct = round((unrealized / cost) * 100.0, 2) if cost > 0 else 0.0

            open_positions.append({
                "ticker": sym,
                "quantity": total_qty,
                "avg_cost_price": avg_cost,
                "total_cost_basis": round(cost, 2),
                "current_price": cp,
                "market_value": mv,
                "unrealized_pnl": unrealized,
                "unrealized_pnl_pct": unrealized_pct
            })
            total_cost_basis += cost
            total_market_value += mv
            total_unrealized_pnl += unrealized

    total_realized_pnl = sum(t["realized_pnl"] for t in closed_trades)
    winning_count = sum(1 for t in closed_trades if t["realized_pnl"] > 0)
    closed_count = len(closed_trades)
    win_rate = round((winning_count / closed_count) * 100.0, 2) if closed_count > 0 else 0.0

    return {
        "open_positions": open_positions,
        "closed_trades": closed_trades,
        "total_cost_basis": round(total_cost_basis, 2),
        "total_market_value": round(total_market_value, 2),
        "total_unrealized_pnl": round(total_unrealized_pnl, 2),
        "total_realized_pnl": round(total_realized_pnl, 2),
        "closed_trades_count": closed_count,
        "winning_trades_count": winning_count,
        "win_rate_pct": win_rate
    }
