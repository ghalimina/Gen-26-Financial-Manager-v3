#!/usr/bin/env python3
# =============================================================================
# portfolio_journal.py — GEN-26 V4.1 Personal Portfolio Transaction Journal
# Authoritative persistent store and FIFO P&L engine for REAL trades.
# 
# ZERO-TRUST SAFETY INVARIANTS:
# 1. 100% independent from gen_decision_log.csv (read-only reference).
# 2. NEVER touches Frozen Core risk gates (Cash Gate, 65% Allocation Gate).
# 3. NEVER modifies SessionManager paper trading counter.
# =============================================================================

import os
import json
import uuid
import datetime
import pandas as pd
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_DIR = os.path.join(BASE_DIR, 'data')
DEFAULT_TRANSACTIONS_FILE = os.path.join(DEFAULT_DATA_DIR, 'my_portfolio_transactions.json')


def get_default_transactions_file() -> str:
    """Returns the canonical path for transactions and ensures directory exists."""
    os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
    return DEFAULT_TRANSACTIONS_FILE


def load_transactions(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Loads all real portfolio transactions from the persistent JSON store."""
    path = file_path or get_default_transactions_file()
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception as e:
        print(f"[WARN] Error reading transactions from {path}: {e}")
        return []


def save_transactions(transactions: List[Dict[str, Any]], file_path: Optional[str] = None) -> bool:
    """Saves real portfolio transactions to the persistent JSON store."""
    path = file_path or get_default_transactions_file()
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(transactions, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] Error saving transactions to {path}: {e}")
        return False


def add_transaction(
    ticker: str,
    action: str,
    quantity: int,
    price: float,
    date: Optional[str] = None,
    source: str = "MANUAL",
    decision_id: Optional[str] = None,
    fees_paid: float = 0.0,
    notes: str = "",
    file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Records a new real portfolio transaction.
    action: 'BUY' or 'SELL'
    source: 'MANUAL' or 'SYSTEM_SUGGESTION'
    """
    ticker_clean = str(ticker).strip().upper()
    if not ticker_clean.endswith('.CA') and not '.' in ticker_clean:
        ticker_clean = f"{ticker_clean}.CA"
        
    action_clean = str(action).strip().upper()
    if action_clean not in ["BUY", "SELL"]:
        raise ValueError(f"Invalid transaction action: {action}. Must be 'BUY' or 'SELL'.")

    qty = int(quantity)
    if qty <= 0:
        raise ValueError("Transaction quantity must be a positive integer.")

    px = float(price)
    if px <= 0:
        raise ValueError("Transaction price must be greater than zero.")

    fees = max(float(fees_paid), 0.0)
    tx_date = date or datetime.datetime.now().strftime("%Y-%m-%d")

    new_tx = {
        "transaction_id": str(uuid.uuid4()),
        "ticker": ticker_clean,
        "action": action_clean,
        "quantity": qty,
        "price": round(px, 4),
        "date": tx_date,
        "source": str(source).strip().upper(),
        "decision_id": str(decision_id).strip() if decision_id else None,
        "fees_paid": round(fees, 2),
        "notes": str(notes).strip(),
        "created_at": datetime.datetime.now().isoformat()
    }

    transactions = load_transactions(file_path)
    transactions.append(new_tx)
    save_transactions(transactions, file_path)
    return new_tx


def update_transaction(
    transaction_id: str,
    file_path: Optional[str] = None,
    **kwargs
) -> bool:
    """Updates fields of an existing transaction by transaction_id."""
    transactions = load_transactions(file_path)
    updated = False
    for tx in transactions:
        if tx.get("transaction_id") == transaction_id:
            for k, v in kwargs.items():
                if k in ["ticker", "action"]:
                    tx[k] = str(v).strip().upper()
                elif k in ["quantity"]:
                    tx[k] = int(v)
                elif k in ["price", "fees_paid"]:
                    tx[k] = float(v)
                elif k in ["date", "source", "decision_id", "notes"]:
                    tx[k] = v
            updated = True
            break

    if updated:
        return save_transactions(transactions, file_path)
    return False


def delete_transaction(transaction_id: str, file_path: Optional[str] = None) -> bool:
    """Deletes a transaction by transaction_id."""
    transactions = load_transactions(file_path)
    initial_len = len(transactions)
    transactions = [tx for tx in transactions if tx.get("transaction_id") != transaction_id]
    if len(transactions) < initial_len:
        return save_transactions(transactions, file_path)
    return False


def compute_portfolio_performance(
    transactions: List[Dict[str, Any]],
    live_quotes_map: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Derives real portfolio holdings, FIFO closed trade P&L, weighted-average cost basis,
    unrealized P&L, win rate, and equity curve from the transaction history.
    """
    if live_quotes_map is None:
        live_quotes_map = {}

    if not transactions:
        return {
            "open_positions": [],
            "closed_trades": [],
            "total_realized_pnl": 0.0,
            "total_unrealized_pnl": 0.0,
            "total_pnl_egp": 0.0,
            "total_cost_basis": 0.0,
            "total_market_value": 0.0,
            "total_unrealized_pnl_pct": 0.0,
            "closed_trades_count": 0,
            "winning_trades_count": 0,
            "win_rate_pct": 0.0,
            "total_fees_paid": 0.0,
            "equity_curve": []
        }

    # Sort transactions chronologically
    sorted_txs = sorted(
        transactions,
        key=lambda x: (x.get("date", ""), x.get("created_at", ""))
    )

    # Group transactions by ticker
    tx_by_ticker: Dict[str, List[Dict[str, Any]]] = {}
    total_fees_paid = 0.0
    for tx in sorted_txs:
        tkr = tx.get("ticker", "").strip().upper()
        if not tkr:
            continue
        tx_by_ticker.setdefault(tkr, []).append(tx)
        total_fees_paid += float(tx.get("fees_paid", 0.0))

    all_closed_trades: List[Dict[str, Any]] = []
    all_open_positions: List[Dict[str, Any]] = []

    total_realized_pnl = 0.0

    for ticker, tx_list in tx_by_ticker.items():
        # FIFO Lot tracking
        buy_lots: List[Dict[str, Any]] = []

        for tx in tx_list:
            act = tx.get("action", "").upper()
            qty = int(tx.get("quantity", 0))
            price = float(tx.get("price", 0.0))
            date = tx.get("date", "")
            tx_id = tx.get("transaction_id", "")
            fees = float(tx.get("fees_paid", 0.0))

            if act == "BUY":
                buy_lots.append({
                    "lot_id": tx_id,
                    "date": date,
                    "original_qty": qty,
                    "remaining_qty": qty,
                    "price": price,
                    "total_fees": fees
                })

            elif act == "SELL":
                remaining_sell_qty = qty
                sell_price = price

                while remaining_sell_qty > 0 and buy_lots:
                    oldest_lot = buy_lots[0]
                    available_qty = oldest_lot["remaining_qty"]
                    match_qty = min(remaining_sell_qty, available_qty)

                    buy_price = oldest_lot["price"]
                    lot_orig_qty = max(oldest_lot["original_qty"], 1)

                    # Prorate fees
                    buy_fee_chunk = (match_qty / lot_orig_qty) * oldest_lot["total_fees"]
                    sell_fee_chunk = (match_qty / qty) * fees if qty > 0 else 0.0

                    gross_pnl = match_qty * (sell_price - buy_price)
                    net_pnl = gross_pnl - (buy_fee_chunk + sell_fee_chunk)
                    cost_chunk = match_qty * buy_price
                    pnl_pct = (gross_pnl / cost_chunk * 100.0) if cost_chunk > 0 else 0.0

                    closed_trade = {
                        "ticker": ticker,
                        "buy_date": oldest_lot["date"],
                        "sell_date": date,
                        "quantity": match_qty,
                        "buy_price": round(buy_price, 2),
                        "sell_price": round(sell_price, 2),
                        "cost_basis": round(cost_chunk, 2),
                        "proceeds": round(match_qty * sell_price, 2),
                        "fees": round(buy_fee_chunk + sell_fee_chunk, 2),
                        "realized_pnl": round(net_pnl, 2),
                        "pnl_pct": round(pnl_pct, 2),
                        "is_win": net_pnl > 0,
                        "buy_transaction_id": oldest_lot["lot_id"],
                        "sell_transaction_id": tx_id
                    }

                    all_closed_trades.append(closed_trade)
                    total_realized_pnl += net_pnl

                    oldest_lot["remaining_qty"] -= match_qty
                    remaining_sell_qty -= match_qty

                    if oldest_lot["remaining_qty"] <= 0:
                        buy_lots.pop(0)

        # Remaining open lots for this ticker
        open_qty = sum(lot["remaining_qty"] for lot in buy_lots)
        if open_qty > 0:
            open_cost_basis = sum(lot["remaining_qty"] * lot["price"] for lot in buy_lots)
            weighted_avg_cost = open_cost_basis / open_qty if open_qty > 0 else 0.0

            # Live price resolution
            q = live_quotes_map.get(ticker)
            live_price = None
            if hasattr(q, "last_price") and q.last_price and q.last_price > 0:
                live_price = float(q.last_price)
            elif isinstance(q, dict) and q.get("last_price", 0) > 0:
                live_price = float(q["last_price"])
            elif isinstance(q, (int, float)) and q > 0:
                live_price = float(q)
            else:
                # Fallback to last buy price
                live_price = weighted_avg_cost

            market_value = open_qty * live_price
            unrealized_pnl = market_value - open_cost_basis
            unrealized_pnl_pct = (unrealized_pnl / open_cost_basis * 100.0) if open_cost_basis > 0 else 0.0

            first_entry_date = buy_lots[0]["date"] if buy_lots else ""

            all_open_positions.append({
                "ticker": ticker,
                "quantity": open_qty,
                "avg_cost_price": round(weighted_avg_cost, 2),
                "total_cost_basis": round(open_cost_basis, 2),
                "current_price": round(live_price, 2),
                "market_value": round(market_value, 2),
                "unrealized_pnl": round(unrealized_pnl, 2),
                "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
                "first_entry_date": first_entry_date,
                "open_lots_count": len(buy_lots)
            })

    # Portfolio level aggregates
    total_unrealized_pnl = sum(pos["unrealized_pnl"] for pos in all_open_positions)
    total_cost_basis = sum(pos["total_cost_basis"] for pos in all_open_positions)
    total_market_value = sum(pos["market_value"] for pos in all_open_positions)
    total_unrealized_pnl_pct = (total_unrealized_pnl / total_cost_basis * 100.0) if total_cost_basis > 0 else 0.0
    total_pnl_egp = total_realized_pnl + total_unrealized_pnl

    closed_count = len(all_closed_trades)
    winning_count = sum(1 for t in all_closed_trades if t["is_win"])
    win_rate = (winning_count / closed_count * 100.0) if closed_count > 0 else 0.0

    # Build Equity Curve Series chronologically
    equity_curve = []
    running_realized = 0.0
    daily_groups = {}
    for t in sorted(all_closed_trades, key=lambda x: x.get("sell_date", "")):
        d = t.get("sell_date", "")
        running_realized += t.get("realized_pnl", 0.0)
        daily_groups[d] = running_realized

    for d, cum_pnl in sorted(daily_groups.items()):
        equity_curve.append({
            "date": d,
            "cumulative_realized_pnl": round(cum_pnl, 2)
        })

    return {
        "open_positions": all_open_positions,
        "closed_trades": all_closed_trades,
        "total_realized_pnl": round(total_realized_pnl, 2),
        "total_unrealized_pnl": round(total_unrealized_pnl, 2),
        "total_pnl_egp": round(total_pnl_egp, 2),
        "total_cost_basis": round(total_cost_basis, 2),
        "total_market_value": round(total_market_value, 2),
        "total_unrealized_pnl_pct": round(total_unrealized_pnl_pct, 2),
        "closed_trades_count": closed_count,
        "winning_trades_count": winning_count,
        "win_rate_pct": round(win_rate, 1),
        "total_fees_paid": round(total_fees_paid, 2),
        "equity_curve": equity_curve
    }
