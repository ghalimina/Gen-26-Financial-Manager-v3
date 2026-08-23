#!/usr/bin/env python3
# =============================================================================
# core/live_execution_firewall.py — GEN-26 Live Execution Safety Firewall
# Hard security firewall ensuring live real-money trading is strictly impossible.
# Any call attempting live routing fails closed immediately.
# =============================================================================

from typing import Dict, Any


class LiveExecutionBlockedError(RuntimeError):
    """Raised when an unauthorized attempt to execute a live real-money order occurs."""
    pass


class LiveExecutionFirewall:
    """
    Guarantees that all execution requests are strictly intercepted, validated,
    and restricted to paper simulation mode.
    """
    ENFORCE_PAPER_MODE = True

    @classmethod
    def assert_paper_mode_only(cls, requested_mode: str = "PAPER"):
        """
        Enforces that only 'PAPER' mode is allowed. Fails closed on any other mode.
        """
        if requested_mode.upper() != "PAPER" or not cls.ENFORCE_PAPER_MODE:
            raise LiveExecutionBlockedError(
                "CRITICAL SECURITY FIREWALL: Live trading is strictly blocked. "
                "GEN-26 is configured for PAPER TRADING ONLY (30-Day Maturation Gate Active)."
            )

    @classmethod
    def validate_execution_safety(cls, order_payload: Dict[str, Any]) -> bool:
        """
        Validates that order is flagged as simulated paper execution.
        """
        cls.assert_paper_mode_only(order_payload.get("mode", "PAPER"))
        if order_payload.get("is_live", False) is True:
            raise LiveExecutionBlockedError("CRITICAL: is_live flag detected as True in paper order payload!")
        return True
