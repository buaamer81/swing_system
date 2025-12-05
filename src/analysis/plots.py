# src/analysis/plots.py

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd


REPORTS_DIR = Path("reports")


def plot_equity_curve_r(ticker: str, df_trades: pd.DataFrame) -> Optional[Path]:
    """
    Rebuilds cumulative R equity curve from trades, saves to PNG.
    """
    if df_trades.empty:
        return None

    df_sorted = df_trades.sort_values("exit_date")
    equity_r = df_sorted["r_result"].cumsum()
    equity_r.index = pd.to_datetime(df_sorted["exit_date"])

    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / f"{ticker.lower()}_equity_r_week6.png"

    plt.figure(figsize=(10, 4))
    equity_r.plot()
    plt.title(f"Equity Curve (R) — {ticker}")
    plt.xlabel("Date")
    plt.ylabel("Cumulative R")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

    return path


def plot_drawdown_curve(ticker: str, df_trades: pd.DataFrame) -> Optional[Path]:
    """
    Drawdown in R, derived from cumulative R equity.
    """
    if df_trades.empty:
        return None

    df_sorted = df_trades.sort_values("exit_date")
    equity_r = df_sorted["r_result"].cumsum()
    equity_r.index = pd.to_datetime(df_sorted["exit_date"])

    running_max = equity_r.cummax()
    drawdown = equity_r - running_max

    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / f"{ticker.lower()}_drawdown_week6.png"

    plt.figure(figsize=(10, 4))
    drawdown.plot()
    plt.title(f"Drawdown (R) — {ticker}")
    plt.xlabel("Date")
    plt.ylabel("Drawdown (R)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

    return path


def plot_r_distribution(ticker: str, df_trades: pd.DataFrame) -> Optional[Path]:
    """
    Histogram of R results per trade.
    """
    if df_trades.empty:
        return None

    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / f"{ticker.lower()}_r_dist_week6.png"

    plt.figure(figsize=(6, 4))
    df_trades["r_result"].hist(bins=20)
    plt.title(f"Distribution of R — {ticker}")
    plt.xlabel("R multiple")
    plt.ylabel("Count of trades")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

    return path


def plot_r_scatter(ticker: str, df_trades: pd.DataFrame) -> Optional[Path]:
    """
    Scatter plot of R result for each trade index.
    """
    if df_trades.empty:
        return None

    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / f"{ticker.lower()}_r_scatter_week6.png"

    plt.figure(figsize=(8, 4))
    plt.scatter(range(len(df_trades)), df_trades["r_result"])
    plt.title(f"R per Trade — {ticker}")
    plt.xlabel("Trade index")
    plt.ylabel("R result")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

    return path
