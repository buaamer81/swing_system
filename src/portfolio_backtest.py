# src/portfolio_backtest.py

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.config import UNIVERSE
from src.analysis.metrics import _compute_max_drawdown_from_r, compute_ticker_metrics_from_df, metrics_to_dict


REPORTS_DIR = Path("reports")


def load_trades_for_universe() -> pd.DataFrame:
    """
    Load all {ticker}_trades.csv files from reports/ and aggregate
    them into a single DataFrame with a 'ticker' column.
    """
    all_trades: List[pd.DataFrame] = []

    for ticker in UNIVERSE:
        path = REPORTS_DIR / f"{ticker.lower()}_trades.csv"
        if not path.exists():
            print(f"[WARN] Missing trades file for {ticker}: {path}")
            continue

        df = pd.read_csv(path)

        # Ensure required columns exist
        required_cols = {
            "entry_date",
            "exit_date",
            "entry_price",
            "exit_price",
            "dollar_pl",
            "r_result",
            "holding_days",
            "hit_target",
            "hit_stop",
        }
        missing = required_cols - set(df.columns)
        if missing:
            print(f"[WARN] Trades file {path} missing columns: {missing}")
            continue

        # Parse dates
        for col in ("entry_date", "exit_date"):
            df[col] = pd.to_datetime(df[col])

        # Ensure ticker column
        if "ticker" not in df.columns:
            df["ticker"] = ticker

        all_trades.append(df)

    if not all_trades:
        print("[ERROR] No trades loaded for any ticker in UNIVERSE.")
        return pd.DataFrame()

    all_trades_df = pd.concat(all_trades, ignore_index=True)
    return all_trades_df


def build_unconstrained_equity_r(all_trades_df: pd.DataFrame) -> pd.Series:
    """
    Build portfolio cumulative R curve assuming we take EVERY trade
    from every ticker (unlimited capital, no max-open-positions constraint).
    """
    df_sorted = all_trades_df.sort_values("exit_date")
    equity_r = df_sorted["r_result"].cumsum()
    equity_r.index = df_sorted["exit_date"]
    equity_r.index = pd.to_datetime(equity_r.index)
    return equity_r


def simulate_max_open_positions(
    all_trades_df: pd.DataFrame,
    max_open_positions: int = 5,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Simulate a simple portfolio rule:
    - Sort trades by entry_date
    - Only take a trade if current open positions < max_open_positions
    - Otherwise, skip the trade

    This is a simplified scheduler: we don't resize risk per trade here,
    we just decide which trades to include/exclude.

    Returns:
        chosen_trades_df: DataFrame of trades we actually take
        equity_r: cumulative R series based on chosen trades (by exit_date)
    """
    if all_trades_df.empty:
        return all_trades_df, pd.Series(dtype=float)

    df = all_trades_df.copy()
    df_sorted = df.sort_values("entry_date").reset_index(drop=True)

    chosen_rows = []
    open_trades: List[Tuple[pd.Timestamp, pd.Timestamp]] = []  # (entry, exit)

    for idx, row in df_sorted.iterrows():
        entry = row["entry_date"]
        exit_ = row["exit_date"]

        # Drop trades that have already closed before this entry
        open_trades = [
            (e, x)
            for (e, x) in open_trades
            if x >= entry
        ]

        if len(open_trades) < max_open_positions:
            # Take this trade
            chosen_rows.append(row)
            open_trades.append((entry, exit_))
        else:
            # Skip this trade due to max-open constraint
            continue

    if not chosen_rows:
        return pd.DataFrame(columns=df.columns), pd.Series(dtype=float)

    chosen_trades_df = pd.DataFrame(chosen_rows)

    # Build equity curve in R using exit_date ordering
    chosen_sorted = chosen_trades_df.sort_values("exit_date")
    equity_r = chosen_sorted["r_result"].cumsum()
    equity_r.index = pd.to_datetime(chosen_sorted["exit_date"])

    return chosen_trades_df, equity_r


def save_equity_plot(equity_r: pd.Series, title: str, filename: str) -> None:
    if equity_r.empty:
        return

    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / filename

    plt.figure(figsize=(10, 4))
    equity_r.plot()
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Cumulative R")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

    print(f"Saved portfolio equity curve: {path}")


def print_metrics_header(label: str):
    print("\n" + "=" * 40)
    print(label)
    print("=" * 40)


def main():
    print("=== Week 7 — Portfolio Backtest (Multi-ticker) ===")

    all_trades_df = load_trades_for_universe()
    if all_trades_df.empty:
        return

    # -------------------------------
    # 1) Unconstrained portfolio (take all trades)
    # -------------------------------
    print_metrics_header("Unconstrained Portfolio (All Trades)")

    # Use the same metrics logic as a "ticker", but with ticker="PORTFOLIO_ALL"
    portfolio_metrics = compute_ticker_metrics_from_df("PORTFOLIO_ALL", all_trades_df)
    metrics_dict = metrics_to_dict(portfolio_metrics)

    for k, v in metrics_dict.items():
        print(f"{k:18}: {v}")

    equity_r_all = build_unconstrained_equity_r(all_trades_df)
    max_dd_all = _compute_max_drawdown_from_r(equity_r_all)
    print(f"max_drawdown_r (from equity): {round(max_dd_all, 2)}")

    save_equity_plot(
        equity_r_all,
        title="Portfolio Equity Curve (R) — Unconstrained",
        filename="portfolio_equity_unconstrained_r_week7.png",
    )

    # -------------------------------
    # 2) Constrained portfolio (max open positions)
    # -------------------------------
    max_open = 5  # you can change this
    print_metrics_header(f"Constrained Portfolio (max_open_positions = {max_open})")

    constrained_df, equity_r_constrained = simulate_max_open_positions(
        all_trades_df,
        max_open_positions=max_open,
    )

    if constrained_df.empty:
        print("No trades after applying max-open-positions rule.")
        return

    portfolio_constrained_metrics = compute_ticker_metrics_from_df(
        f"PORTFOLIO_MAX{max_open}",
        constrained_df,
    )
    constrained_metrics_dict = metrics_to_dict(portfolio_constrained_metrics)

    for k, v in constrained_metrics_dict.items():
        print(f"{k:18}: {v}")

    max_dd_constrained = _compute_max_drawdown_from_r(equity_r_constrained)
    print(f"max_drawdown_r (from equity): {round(max_dd_constrained, 2)}")

    save_equity_plot(
        equity_r_constrained,
        title=f"Portfolio Equity Curve (R) — max_open={max_open}",
        filename=f"portfolio_equity_max{max_open}_r_week7.png",
    )

    print("\nDone. Check the 'reports/' folder for portfolio plots.")


if __name__ == "__main__":
    main()
