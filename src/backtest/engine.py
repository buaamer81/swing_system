# src/backtest/engine.py

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd

from src.config import RISK_CONFIG
from src.signals.engine import _breakout_signal_from_row, load_features, Signal


# --------------------------
# Data structures
# --------------------------


@dataclass
class Trade:
    ticker: str
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float
    shares: float
    dollar_pl: float
    r_result: float
    holding_days: int
    hit_target: bool
    hit_stop: bool
    stop_price: float
    target_price: float
    risk_dollars: float          # how much $ you risked on this trade
    risk_per_share: float


@dataclass
class BacktestResult:
    ticker: str
    trades: List[Trade]
    total_trades: int
    win_rate: float
    expectancy_r: float
    total_pl_dollars: float
    avg_holding: float
    max_drawdown_r: float
    equity_curve_r: pd.Series


# --------------------------
# Core backtest logic
# --------------------------


def backtest_breakout_ticker(
    ticker: str,
    df: Optional[pd.DataFrame] = None,
    account_size: Optional[float] = None,
    risk_pct: Optional[float] = None,
    max_hold_bars: Optional[int] = None,
) -> BacktestResult:
    """Backtest the breakout system for a single ticker.

    - Uses _breakout_signal_from_row for signal logic
    - Enters on the NEXT bar's open
    - Uses ATR-based stop and target from the Signal
    - Holds up to max_hold_bars if neither stop nor target is hit
    """
    if account_size is None:
        account_size = RISK_CONFIG.account_size
    if risk_pct is None:
        risk_pct = RISK_CONFIG.risk_pct
    if max_hold_bars is None:
        max_hold_bars = RISK_CONFIG.max_hold_bars

    if df is None:
        df = load_features(ticker)

    if df.empty:
        return BacktestResult(
            ticker=ticker,
            trades=[],
            total_trades=0,
            win_rate=0.0,
            expectancy_r=0.0,
            total_pl_dollars=0.0,
            avg_holding=0.0,
            max_drawdown_r=0.0,
            equity_curve_r=pd.Series(dtype=float),
        )

    # Ensure sorted by Date
    if "Date" in df.columns:
        df = df.sort_values("Date").reset_index(drop=True)
    else:
        raise ValueError("DataFrame must contain a 'Date' column for backtesting.")

    risk_dollars = account_size * risk_pct

    trades: List[Trade] = []
    equity_values: List[float] = []
    equity_dates: List[pd.Timestamp] = []
    cumulative_r = 0.0

    n = len(df)
    i = 0

    # Single-position per ticker (no overlapping trades on the same symbol)
    while i < n - 1:  # need at least one bar ahead for entry
        row = df.iloc[i]
        signal: Optional[Signal] = _breakout_signal_from_row(ticker, row)

        if signal is None:
            i += 1
            continue

        # We enter on next bar's open
        entry_idx = i + 1
        if entry_idx >= n:
            break

        entry_row = df.iloc[entry_idx]
        entry_date = pd.to_datetime(entry_row["Date"])
        entry_price = float(entry_row["Open"])

        risk_per_share = entry_price - signal.stop
        if risk_per_share <= 0:
            i += 1
            continue

        shares = risk_dollars / risk_per_share
        shares = np.floor(shares)
        if shares <= 0:
            i += 1
            continue

        stop_price = signal.stop
        target_price = signal.target

        hit_target = False
        hit_stop = False

        exit_idx: Optional[int] = None
        exit_price: Optional[float] = None
        exit_date: Optional[pd.Timestamp] = None

        # Simulate forward for up to max_hold_bars bars
        last_sim_idx = min(n - 1, entry_idx + max_hold_bars)

        for j in range(entry_idx, last_sim_idx + 1):
            bar = df.iloc[j]
            bar_date = pd.to_datetime(bar["Date"])
            bar_high = float(bar["High"])
            bar_low = float(bar["Low"])
            bar_close = float(bar["Close"])

            # Check stop first (conservative)
            if bar_low <= stop_price:
                exit_idx = j
                exit_date = bar_date
                exit_price = stop_price
                hit_stop = True
                hit_target = False
                break

            # Then check target
            if bar_high >= target_price:
                exit_idx = j
                exit_date = bar_date
                exit_price = target_price
                hit_target = True
                hit_stop = False
                break

            # Reached last bar of holding window without hit
            if j == last_sim_idx:
                exit_idx = j
                exit_date = bar_date
                exit_price = bar_close
                hit_target = False
                hit_stop = False

        if exit_idx is None or exit_price is None or exit_date is None:
            # Safety fallback; shouldn't happen
            i += 1
            continue

        dollar_pl = (exit_price - entry_price) * shares
        r_result = dollar_pl / (risk_per_share * shares)
        holding_days = int((exit_date - entry_date).days)

        trade = Trade(
            ticker=ticker,
            entry_date=entry_date,
            exit_date=exit_date,
            entry_price=entry_price,
            exit_price=exit_price,
            shares=float(shares),
            dollar_pl=float(dollar_pl),
            r_result=float(r_result),
            holding_days=holding_days,
            hit_target=hit_target,
            hit_stop=hit_stop,
            stop_price=float(stop_price),
            target_price=float(target_price),
            risk_dollars=float(risk_dollars),
            risk_per_share=float(risk_per_share),
        )
        trades.append(trade)

        cumulative_r += r_result
        equity_values.append(cumulative_r)
        equity_dates.append(exit_date)

        # Move index to after the exit bar (no overlapping trades per ticker)
        i = exit_idx + 1

    # Build equity curve series
    if equity_values:
        equity_curve_r = pd.Series(equity_values, index=pd.to_datetime(equity_dates))
        equity_curve_r = equity_curve_r.sort_index()
    else:
        equity_curve_r = pd.Series(dtype=float)

    total_trades = len(trades)

    if total_trades > 0:
        wins = [t for t in trades if t.dollar_pl > 0]
        # losses = [t for t in trades if t.dollar_pl < 0]  # not used directly now

        win_rate = len(wins) / total_trades * 100.0
        expectancy_r = float(np.mean([t.r_result for t in trades]))
        total_pl_dollars = float(sum(t.dollar_pl for t in trades))
        avg_holding = float(np.mean([t.holding_days for t in trades]))
    else:
        win_rate = 0.0
        expectancy_r = 0.0
        total_pl_dollars = 0.0
        avg_holding = 0.0

    # Max drawdown in R
    if not equity_curve_r.empty:
        running_max = equity_curve_r.cummax()
        drawdown = equity_curve_r - running_max
        max_drawdown_r = float(drawdown.min())
    else:
        max_drawdown_r = 0.0

    return BacktestResult(
        ticker=ticker,
        trades=trades,
        total_trades=total_trades,
        win_rate=win_rate,
        expectancy_r=expectancy_r,
        total_pl_dollars=total_pl_dollars,
        avg_holding=avg_holding,
        max_drawdown_r=max_drawdown_r,
        equity_curve_r=equity_curve_r,
    )
