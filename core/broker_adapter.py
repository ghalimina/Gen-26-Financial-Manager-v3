#!/usr/bin/env python3
# =============================================================================
# core/broker_adapter.py — GEN-26 Institutional Broker Abstraction Layer
# Provides unified ExecutionInterface, local PaperBrokerAdapter, AdvisoryBrokerAdapter,
# and graceful schema for FutureOfficialBrokerAdapter (No browser/UI hacks).
# =============================================================================

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import datetime
import uuid


class OrderStatus:
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class ExecutionInterface(ABC):
    """
    Abstract Base Class for Broker Execution Adapters.
    """

    @abstractmethod
    def validate_order(self, symbol: str, side: str, quantity: int, price: float) -> Dict[str, Any]:
        pass

    @abstractmethod
    def place_order(self, symbol: str, side: str, quantity: int, price: float, order_type: str = "LIMIT") -> Dict[str, Any]:
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_positions(self) -> Dict[str, int]:
        pass

    @abstractmethod
    def get_cash(self) -> float:
        pass

    @abstractmethod
    def reconcile(self) -> Dict[str, Any]:
        pass


class PaperBrokerAdapter(ExecutionInterface):
    """
    Full local execution simulator tracking cash, positions, slippage, and fees.
    """

    def __init__(self, initial_cash: float = 100_000.0, fee_pct: float = 0.00175, slippage_pct: float = 0.0010):
        self.cash = float(initial_cash)
        self.initial_cash = float(initial_cash)
        self.fee_pct = fee_pct
        self.slippage_pct = slippage_pct
        self.positions: Dict[str, int] = {}
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.execution_log: List[Dict[str, Any]] = []

    def validate_order(self, symbol: str, side: str, quantity: int, price: float) -> Dict[str, Any]:
        if quantity <= 0:
            return {"valid": False, "reason": "QUANTITY_MUST_BE_POSITIVE"}
        if price <= 0:
            return {"valid": False, "reason": "PRICE_MUST_BE_POSITIVE"}

        side = side.upper()
        if side == "BUY":
            cost = quantity * price * (1.0 + self.fee_pct + self.slippage_pct)
            if cost > self.cash:
                return {"valid": False, "reason": "INSUFFICIENT_CASH_SOLVENCY"}
        elif side == "SELL":
            current_qty = self.positions.get(symbol, 0)
            if quantity > current_qty:
                return {"valid": False, "reason": "INSUFFICIENT_POSITION_QUANTITY"}
        else:
            return {"valid": False, "reason": "INVALID_SIDE"}

        return {"valid": True, "reason": "OK"}

    def place_order(self, symbol: str, side: str, quantity: int, price: float, order_type: str = "LIMIT") -> Dict[str, Any]:
        val = self.validate_order(symbol, side, quantity, price)
        order_id = f"PAPER-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.datetime.now().isoformat()

        if not val["valid"]:
            record = {
                "order_id": order_id,
                "symbol": symbol,
                "side": side.upper(),
                "quantity": quantity,
                "price": price,
                "order_type": order_type,
                "status": OrderStatus.REJECTED,
                "rejection_reason": val["reason"],
                "timestamp": now_iso
            }
            self.orders[order_id] = record
            return record

        side = side.upper()
        if side == "BUY":
            effective_price = round(price * (1.0 + self.slippage_pct), 3)
            fee = round(quantity * effective_price * self.fee_pct, 2)
            total_outlay = round((quantity * effective_price) + fee, 2)
            self.cash -= total_outlay
            self.positions[symbol] = self.positions.get(symbol, 0) + quantity
        else: # SELL
            effective_price = round(price * (1.0 - self.slippage_pct), 3)
            fee = round(quantity * effective_price * self.fee_pct, 2)
            net_proceeds = round((quantity * effective_price) - fee, 2)
            self.cash += net_proceeds
            self.positions[symbol] -= quantity
            if self.positions[symbol] == 0:
                del self.positions[symbol]

        record = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "requested_price": price,
            "fill_price": effective_price,
            "fee": fee,
            "order_type": order_type,
            "status": OrderStatus.FILLED,
            "timestamp": now_iso
        }
        self.orders[order_id] = record
        self.execution_log.append(record)
        return record

    def cancel_order(self, order_id: str) -> bool:
        if order_id in self.orders and self.orders[order_id]["status"] == OrderStatus.PENDING:
            self.orders[order_id]["status"] = OrderStatus.CANCELLED
            return True
        return False

    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        return self.orders.get(order_id)

    def get_positions(self) -> Dict[str, int]:
        return dict(self.positions)

    def get_cash(self) -> float:
        return round(self.cash, 2)

    def reconcile(self) -> Dict[str, Any]:
        return {
            "cash": self.get_cash(),
            "positions": self.get_positions(),
            "total_orders": len(self.orders),
            "executed_orders": len(self.execution_log),
            "reconciliation_status": "MATCHED"
        }


class AdvisoryBrokerAdapter(ExecutionInterface):
    """
    Generates structured order recommendations with user confirmation workflow.
    """

    def __init__(self):
        self.recommendations: List[Dict[str, Any]] = []

    def validate_order(self, symbol: str, side: str, quantity: int, price: float) -> Dict[str, Any]:
        return {"valid": quantity > 0 and price > 0, "reason": "OK" if quantity > 0 and price > 0 else "INVALID_PARAMS"}

    def place_order(self, symbol: str, side: str, quantity: int, price: float, order_type: str = "LIMIT") -> Dict[str, Any]:
        rec_id = f"ADVISORY-{uuid.uuid4().hex[:8].upper()}"
        record = {
            "recommendation_id": rec_id,
            "symbol": symbol,
            "side": side.upper(),
            "quantity": quantity,
            "price": price,
            "order_type": order_type,
            "status": "AWAITING_MANUAL_EXECUTION",
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.recommendations.append(record)
        return record

    def cancel_order(self, order_id: str) -> bool:
        return True

    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        for r in self.recommendations:
            if r.get("recommendation_id") == order_id:
                return r
        return None

    def get_positions(self) -> Dict[str, int]:
        return {}

    def get_cash(self) -> float:
        return 0.0

    def reconcile(self) -> Dict[str, Any]:
        return {"status": "ADVISORY_MODE_ACTIVE", "pending_recommendations": len(self.recommendations)}


class FutureOfficialBrokerAdapter(ExecutionInterface):
    """
    Placeholder schema for official broker API (e.g. Thndr / EFG Hermes official institutional endpoints).
    Strictly disabled and marked BLOCKED_EXTERNAL_DEPENDENCY until authorized public API exists.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.is_connected = False

    def validate_order(self, symbol: str, side: str, quantity: int, price: float) -> Dict[str, Any]:
        return {"valid": False, "reason": "BLOCKED_EXTERNAL_DEPENDENCY: No authorized official broker API"}

    def place_order(self, symbol: str, side: str, quantity: int, price: float, order_type: str = "LIMIT") -> Dict[str, Any]:
        raise NotImplementedError("Live automated broker execution is BLOCKED pending official API authorization.")

    def cancel_order(self, order_id: str) -> bool:
        return False

    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        return None

    def get_positions(self) -> Dict[str, int]:
        return {}

    def get_cash(self) -> float:
        return 0.0

    def reconcile(self) -> Dict[str, Any]:
        return {"status": "BLOCKED_EXTERNAL_DEPENDENCY"}
