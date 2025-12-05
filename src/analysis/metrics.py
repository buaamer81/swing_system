# src/analysis/metrics.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

import numpy as np
import pandas as pd


@dataclass
class TickerMetrics:
    ticker: str
    total_trades: int
    win_rate: float
    loss_rate: float
    avg_r: float
    expectancy_r: float
    profit_factor: float
    max_drawdown_r: float
    avg_holding_days: float
    trades_per_year: float
    hit_target_pct: float
    hit_stop_pct: float


def _compute_max_drawdown_from_r(equity_r: pd.Series) -> float:
    """
    equity_r: cumulative R over time (like your equity_curve_r)
    returns max drawdown in R units (negative number or 0)
    """
    if equity_r.empty:
        return 0.0

    running_max = equity_r.cummax()
    drawdown = equity_r - running_max
    return float(drawdown.min())


def compute_ticker_metrics_from_df(ticker: str, df: pd.DataFrame) -> TickerMetrics:
    """
    df: trades dataframe as loaded from reports/{ticker}_trades.csv
        expected columns:
          - entry_date, exit_date (datetime)
          - dollar_pl
          - r_result
          - holding_days
          - hit_target (bool)
          - hit_stop (bool)
    """

    if df.empty:
        return TickerMetrics(
            ticker=ticker,
            total_trades=0,
            win_rate=0.0,
            loss_rate=0.0,
            avg_r=0.0,
            expectancy_r=0.0,
            profit_factor=0.0,
            max_drawdown_r=0.0,
            avg_holding_days=0.0,
            trades_per_year=0.0,
            hit_target_pct=0.0,
            hit_stop_pct=0.0,
        )

    total_trades = len(df)

    r_values = df["r_result"].astype(float)
    dollar_pl = df["dollar_pl"].astype(float)

    wins = dollar_pl > 0
    losses = dollar_pl < 0

    n_wins = wins.sum()
    n_losses = losses.sum()

    win_rate = 100.0 * n_wins / total_trades
    loss_rate = 100.0 * n_losses / total_trades

    avg_r = float(r_values.mean())
    expectancy_r = avg_r  # same thing: avg R per trade

    gross_wins = dollar_pl[wins].sum()
    gross_losses = -dollar_pl[losses].sum()  # make positive

    if gross_losses > 0:
        profit_factor = float(gross_wins / gross_losses)
    else:
        profit_factor = float("inf") if gross_wins > 0 else 0.0

    avg_holding_days = float(df["holding_days"].mean())

    # Approximate trades per year based on time span
    start_date = pd.to_datetime(df["entry_date"]).min()
    end_date = pd.to_datetime(df["exit_date"]).max()
    days_span = (end_date - start_date).days
    years_span = days_span / 365.25 if days_span > 0 else 1.0
    trades_per_year = total_trades / years_span

    # Build equity curve in R
    # sort by exit_date to get chronological curve
    df_sorted = df.sort_values("exit_date")
    equity_r = df_sorted["r_result"].cumsum()
    equity_r.index = pd.to_datetime(df_sorted["exit_date"])

    max_drawdown_r = _compute_max_drawdown_from_r(equity_r)

    # Hit target/stop percentages
    hit_target_pct = 100.0 * df["hit_target"].sum() / total_trades
    hit_stop_pct = 100.0 * df["hit_stop"].sum() / total_trades

    return TickerMetrics(
        ticker=ticker,
        total_trades=total_trades,
        win_rate=win_rate,
        loss_rate=loss_rate,
        avg_r=avg_r,
        expectancy_r=expectancy_r,
        profit_factor=profit_factor,
        max_drawdown_r=max_drawdown_r,
        avg_holding_days=avg_holding_days,
        trades_per_year=trades_per_year,
        hit_target_pct=hit_target_pct,
        hit_stop_pct=hit_stop_pct,
    )


def metrics_to_dict(m: TickerMetrics) -> Dict[str, Any]:
    """Helper to print or serialize metrics."""
    return {
        "ticker": m.ticker,
        "total_trades": m.total_trades,
        "win_rate": round(m.win_rate, 2),
        "loss_rate": round(m.loss_rate, 2),
        "avg_r": round(m.avg_r, 3),
        "expectancy_r": round(m.expectancy_r, 3),
        "profit_factor": round(m.profit_factor, 3) if m.profit_factor != float("inf") else float("inf"),
        "max_drawdown_r": round(m.max_drawdown_r, 2),
        "avg_holding_days": round(m.avg_holding_days, 1),
        "trades_per_year": round(m.trades_per_year, 1),
        "hit_target_pct": round(m.hit_target_pct, 1),
        "hit_stop_pct": round(m.hit_stop_pct, 1),
    }
