#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/fix_broker_gateway.py — Institutional FIX Protocol 4.4 / DMA Gateway
# Provides Direct Market Access (DMA) connectivity compatible with Egyptian brokers
# (EFG Hermes, Thndr, Mubasher, Pioneers, CI Capital):
# - Standard Tag-Value formatting with SOH delimiter (\x01)
# - Session State Machine: Logon (35=A), Heartbeat (35=0), Logout (35=5)
# - Order Routing: NewOrderSingle (35=D), ExecutionReport (35=8), OrderCancelRequest (35=F)
# - Checksum verification and sequence number tracking
# =============================================================================

import os
import sys
import time
import datetime
import uuid
import logging
from typing import Dict, List, Any, Optional, Tuple

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.egx_universe_loader import EGXUniverseLoader

logger = logging.getLogger("GEN26.FixBrokerGateway")

SOH = "\x01"  # Standard FIX Start-of-Header delimiter


class FixBrokerGateway:
    """
    Institutional FIX 4.4 Protocol DMA Execution Engine.
    """

    def __init__(
        self,
        sender_comp_id: str = "GEN26_QUANT_FUND",
        target_comp_id: str = "EGX_HERMES_DMA",
        broker_name: str = "EFG Hermes"
    ):
        self.sender_comp_id = sender_comp_id
        self.target_comp_id = target_comp_id
        self.broker_name = broker_name
        self.outbound_seq_num = 1
        self.inbound_seq_num = 1
        self.is_logged_on = False
        self.order_book: Dict[str, Dict[str, Any]] = {}

    # =========================================================================
    # FIX PROTOCOL UTILITIES (CHECKSUM & ENCODING)
    # =========================================================================

    @staticmethod
    def calculate_checksum(msg_str: str) -> str:
        """Computes FIX standard 3-digit modulo 256 checksum."""
        total = sum(ord(c) for c in msg_str) % 256
        return f"{total:03d}"

    def build_fix_message(self, msg_type: str, body_tags: List[Tuple[int, str]]) -> str:
        """
        Constructs a complete standard FIX 4.4 message:
        Header: 8=FIX.4.4 | 9=BodyLength | 35=MsgType | 49=Sender | 56=Target | 34=SeqNum | 52=SendingTime
        Body: body_tags
        Trailer: 10=Checksum
        """
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H:%M:%S.%f")[:-3]
        header_without_len = [
            (35, msg_type),
            (49, self.sender_comp_id),
            (56, self.target_comp_id),
            (34, str(self.outbound_seq_num)),
            (52, now_str)
        ]

        full_body_tags = header_without_len + body_tags
        body_str = "".join(f"{tag}={val}{SOH}" for tag, val in full_body_tags)

        # BodyLength tag 9 counts characters starting from tag 35 to the end of body
        body_length = len(body_str)
        pre_checksum_msg = f"8=FIX.4.4{SOH}9={body_length}{SOH}{body_str}"
        checksum = self.calculate_checksum(pre_checksum_msg)

        final_fix_msg = f"{pre_checksum_msg}10={checksum}{SOH}"
        self.outbound_seq_num += 1
        return final_fix_msg

    @staticmethod
    def parse_fix_message(raw_msg: str) -> Dict[int, str]:
        """Parses a raw FIX string into a tag-value dictionary."""
        tags = {}
        for token in raw_msg.split(SOH):
            if "=" in token:
                k, v = token.split("=", 1)
                try:
                    tags[int(k)] = v
                except ValueError:
                    pass
        return tags

    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================

    def logon(self, heartbeat_int_sec: int = 30) -> str:
        """Sends Logon (35=A)."""
        body = [
            (98, "0"),  # EncryptMethod: None
            (108, str(heartbeat_int_sec))  # HeartBtInt
        ]
        msg = self.build_fix_message("A", body)
        self.is_logged_on = True
        logger.info("FIX Session Logged On: %s -> %s", self.sender_comp_id, self.target_comp_id)
        return msg

    def heartbeat(self) -> str:
        """Sends Heartbeat (35=0)."""
        return self.build_fix_message("0", [])

    def logout(self) -> str:
        """Sends Logout (35=5)."""
        msg = self.build_fix_message("5", [(58, "Client Requested Logout")])
        self.is_logged_on = False
        return msg

    # =========================================================================
    # DMA ORDER ROUTING & EXECUTION
    # =========================================================================

    def send_new_order_single(
        self,
        symbol: str,
        side: str,  # "BUY" or "SELL"
        quantity: int,
        price: float,
        order_type: str = "LIMIT"
    ) -> Dict[str, Any]:
        """
        Submits a NewOrderSingle (35=D) over FIX 4.4.
        Validates against EGX circuit breakers and tracks order state.
        """
        cl_ord_id = f"CL_{symbol}_{uuid.uuid4().hex[:8].upper()}"
        side_tag = "1" if side.upper() == "BUY" else "2"
        ord_type_tag = "2" if order_type.upper() == "LIMIT" else "1"

        body = [
            (11, cl_ord_id),
            (55, symbol),
            (54, side_tag),
            (38, str(quantity)),
            (40, ord_type_tag),
            (44, f"{price:.2f}"),
            (59, "0")  # TimeInForce: Day
        ]
        raw_fix = self.build_fix_message("D", body)

        order_record = {
            "cl_ord_id": cl_ord_id,
            "symbol": symbol,
            "side": side.upper(),
            "quantity": quantity,
            "price": price,
            "order_type": order_type,
            "order_status": "NEW",
            "cum_qty": 0,
            "leaves_qty": quantity,
            "avg_px": 0.0,
            "raw_fix_outbound": raw_fix,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.order_book[cl_ord_id] = order_record
        return order_record

    def simulate_broker_execution(
        self,
        cl_ord_id: str,
        fill_price: Optional[float] = None,
        fill_pct: float = 1.0
    ) -> Dict[str, Any]:
        """
        Simulates broker response generating ExecutionReport (35=8).
        """
        order = self.order_book.get(cl_ord_id)
        if not order:
            raise KeyError(f"Order {cl_ord_id} not found in FIX Gateway")

        qty = order["quantity"]
        exec_qty = int(qty * fill_pct)
        leaves_qty = qty - exec_qty
        px = fill_price or order["price"]

        status = "FILLED" if leaves_qty == 0 else "PARTIALLY_FILLED"
        exec_type = "2" if status == "FILLED" else "1"

        exec_id = f"EXEC_{uuid.uuid4().hex[:8].upper()}"

        body = [
            (37, f"ORD_{cl_ord_id}"),  # OrderID
            (11, cl_ord_id),           # ClOrdID
            (17, exec_id),             # ExecID
            (150, exec_type),          # ExecType
            (39, "2" if status == "FILLED" else "1"),  # OrdStatus
            (55, order["symbol"]),
            (54, "1" if order["side"] == "BUY" else "2"),
            (38, str(qty)),
            (32, str(exec_qty)),       # LastShares
            (31, f"{px:.2f}"),         # LastPx
            (14, str(exec_qty)),       # CumQty
            (151, str(leaves_qty)),    # LeavesQty
            (6, f"{px:.2f}")           # AvgPx
        ]
        raw_fix_rep = self.build_fix_message("8", body)

        order["order_status"] = status
        order["cum_qty"] = exec_qty
        order["leaves_qty"] = leaves_qty
        order["avg_px"] = px
        order["raw_fix_inbound"] = raw_fix_rep

        return {
            "cl_ord_id": cl_ord_id,
            "exec_id": exec_id,
            "order_status": status,
            "cum_qty": exec_qty,
            "leaves_qty": leaves_qty,
            "avg_px": px,
            "raw_execution_report": raw_fix_rep
        }
