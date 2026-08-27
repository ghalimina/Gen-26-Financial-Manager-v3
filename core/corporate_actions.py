#!/usr/bin/env python3
# =============================================================================
# core/corporate_actions.py — GEN-26 Corporate Actions Historical Adjuster
# Adjusts historical OHLCV bar data backwards for Stock Splits and Cash Dividends
# to prevent artificial volatility spikes, distorted ATRs, and false ML triggers.
# =============================================================================

import os
import sys
import datetime
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

logger = logging.getLogger("GEN26.CorporateActionsAdjuster")


class CorporateActionsAdjuster:
    """
    Institutional Backward Adjustment Engine for Corporate Actions (Splits & Dividends).
    
    Mathematical Principles:
    1. Stock Split on Date t (Split Ratio R, e.g., 2.0 for 2-for-1):
       For all historical bars i < t:
         P_adj[i] = P_raw[i] / R
         V_adj[i] = V_raw[i] * R
       For all bars i >= t:
         P_adj[i] = P_raw[i]
         V_adj[i] = V_raw[i]

    2. Cash Dividend on Date t (Dividend amount D, e.g., 2.00 EGP):
       Let P_close_prior = Close price of the bar immediately preceding Date t.
       Adjustment Factor F = 1.0 - (D / P_close_prior)
       For all historical bars i < t:
         P_adj[i] = P_raw[i] * F
       For all bars i >= t:
         P_adj[i] = P_raw[i]
    """

    @classmethod
    def adjust_ohlcv_dataframe(
        cls,
        df: pd.DataFrame,
        actions_df: Optional[pd.DataFrame] = None,
        ticker: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Applies backward adjustments to a historical OHLCV DataFrame for splits and dividends.
        
        Args:
            df: DataFrame containing price columns ('Open', 'High', 'Low', 'Close', 'Volume')
                or lowercase equivalents. Index should be DatetimeIndex or have a 'date' column.
            actions_df: Optional DataFrame with 'Stock Splits' and 'Dividends' columns.
            ticker: Optional symbol to extract actions if actions_df is not provided.
            
        Returns:
            Adjusted DataFrame with smoothed price and volume series.
        """
        if df is None or len(df) == 0:
            return df

        adj_df = df.copy()

        # Standardize column naming
        col_map = {}
        for c in adj_df.columns:
            cl = str(c).lower().strip()
            if cl in ["open", "open_price"]:
                col_map[c] = "Open"
            elif cl in ["high", "high_price"]:
                col_map[c] = "High"
            elif cl in ["low", "low_price"]:
                col_map[c] = "Low"
            elif cl in ["close", "close_price"]:
                col_map[c] = "Close"
            elif cl in ["volume", "vol"]:
                col_map[c] = "Volume"
        
        if col_map:
            adj_df = adj_df.rename(columns=col_map)

        # Standardize index to DatetimeIndex if possible
        if not isinstance(adj_df.index, pd.DatetimeIndex):
            date_col = None
            for c in ["market_date", "Date", "date", "timestamp"]:
                if c in adj_df.columns:
                    date_col = c
                    break
            if date_col:
                adj_df.index = pd.to_datetime(adj_df[date_col])
            else:
                try:
                    adj_df.index = pd.to_datetime(adj_df.index)
                except Exception:
                    pass

        # Sort ascending chronologically
        adj_df = adj_df.sort_index()

        # If actions_df is not supplied and ticker is given, query yfinance actions
        if actions_df is None and ticker:
            actions_df = cls._fetch_actions_for_ticker(ticker)

        if actions_df is None or len(actions_df) == 0:
            return adj_df

        # Standardize actions_df index
        if not isinstance(actions_df.index, pd.DatetimeIndex):
            for c in ["Date", "date", "market_date"]:
                if c in actions_df.columns:
                    actions_df.index = pd.to_datetime(actions_df[c])
                    break
            else:
                try:
                    actions_df.index = pd.to_datetime(actions_df.index)
                except Exception:
                    pass

        # Normalize timezone awareness between df and actions
        if isinstance(adj_df.index, pd.DatetimeIndex) and isinstance(actions_df.index, pd.DatetimeIndex):
            if adj_df.index.tz is not None:
                adj_df.index = adj_df.index.tz_localize(None)
            if actions_df.index.tz is not None:
                actions_df.index = actions_df.index.tz_localize(None)

        # Iterate through corporate actions from most recent to oldest
        sorted_actions = actions_df.sort_index(ascending=False)

        for act_date, row in sorted_actions.iterrows():
            split_ratio = 0.0
            dividend_amt = 0.0

            if "Stock Splits" in row:
                split_ratio = float(row["Stock Splits"] or 0.0)
            elif "splits" in row:
                split_ratio = float(row["splits"] or 0.0)

            if "Dividends" in row:
                dividend_amt = float(row["Dividends"] or 0.0)
            elif "dividends" in row:
                dividend_amt = float(row["dividends"] or 0.0)

            # 1. Apply Stock Split Adjustment
            # A split of 2 means 1 share became 2 shares (ratio = 2.0).
            # Prices before split date should be divided by 2.0.
            # Volume before split date should be multiplied by 2.0.
            if split_ratio > 0.0 and split_ratio != 1.0:
                mask_prior = adj_df.index < act_date
                if mask_prior.any():
                    for price_col in ["Open", "High", "Low", "Close"]:
                        if price_col in adj_df.columns:
                            adj_df.loc[mask_prior, price_col] = adj_df.loc[mask_prior, price_col] / split_ratio
                    if "Volume" in adj_df.columns:
                        adj_df.loc[mask_prior, "Volume"] = adj_df.loc[mask_prior, "Volume"] * split_ratio

            # 2. Apply Cash Dividend Adjustment
            if dividend_amt > 0.0:
                mask_prior = adj_df.index < act_date
                if mask_prior.any():
                    prior_bars = adj_df.loc[mask_prior]
                    if len(prior_bars) > 0 and "Close" in prior_bars.columns:
                        p_close_prior = float(prior_bars["Close"].iloc[-1])
                        if p_close_prior > dividend_amt:
                            div_factor = 1.0 - (dividend_amt / p_close_prior)
                            div_factor = max(0.10, min(1.0, div_factor))
                            for price_col in ["Open", "High", "Low", "Close"]:
                                if price_col in adj_df.columns:
                                    adj_df.loc[mask_prior, price_col] = adj_df.loc[mask_prior, price_col] * div_factor

        return adj_df

    @classmethod
    def _fetch_actions_for_ticker(cls, ticker: str) -> Optional[pd.DataFrame]:
        """Queries yfinance for .actions DataFrame containing Dividends & Splits."""
        try:
            import yfinance as yf
            from data.universe_manager import UniverseManager
            clean_sym = ticker.upper().strip()
            yf_sym = UniverseManager.get_yfinance_ticker(clean_sym)
            if not yf_sym.endswith(".CA") and "." not in yf_sym:
                yf_sym = f"{yf_sym}.CA"

            t = yf.Ticker(yf_sym)
            actions = t.actions
            if actions is not None and len(actions) > 0:
                return actions
        except Exception as e:
            logger.debug(f"Could not fetch actions for {ticker}: {e}")
        return None

    @classmethod
    def fetch_and_adjust_historical_bars(
        cls,
        ticker: str,
        period: str = "6mo",
        min_bars: int = 20
    ) -> Optional[pd.DataFrame]:
        """
        Fetches historical data via yfinance, extracts actions, and applies backward adjustments.
        """
        try:
            import yfinance as yf
            from data.universe_manager import UniverseManager
            clean_sym = ticker.upper().strip()
            yf_sym = UniverseManager.get_yfinance_ticker(clean_sym)
            if not yf_sym.endswith(".CA") and "." not in yf_sym:
                yf_sym = f"{yf_sym}.CA"

            t = yf.Ticker(yf_sym)
            hist = t.history(period=period)
            if hist is None or len(hist) < min_bars:
                return None

            actions = None
            try:
                actions = t.actions
            except Exception:
                pass

            adjusted_df = cls.adjust_ohlcv_dataframe(hist, actions_df=actions, ticker=clean_sym)
            return adjusted_df
        except Exception as e:
            logger.debug(f"Error fetching/adjusting bars for {ticker}: {e}")
            return None
