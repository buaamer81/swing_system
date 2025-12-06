# src/week8_sanity_check.py

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

from src.config import UNIVERSE
from src.analysis.metrics import compute_ticker_metrics_from_df, metrics_to_dict


REPORTS_DIR = Path("reports")


def load_trades_csv(ticker: str) -> pd.DataFrame:
    """
    Load per-ticker trades CSV produced by backtest_breakout.py

    Expected path: reports/{ticker.lower()}_trades.csv
    """
    path = REPORTS_DIR / f"{ticker.lower()}_trades.csv"
    if not path.exists():
        print(f"[WARN] No trades file found for {ticker}: {path}")
        return pd.DataFrame()

    df = pd.read_csv(path)
    if df.empty:
        print(f"[WARN] Trades CSV for {ticker} is empty.")
    return df


def collect_ticker_metrics() -> pd.DataFrame:
    """
    For each ticker in UNIVERSE, compute Week-6 style metrics from trades.
    Returns a DataFrame with one row per ticker.
    """
    rows: List[Dict[str, Any]] = []

    for ticker in UNIVERSE:
        print(f"\n=== Analyzing {ticker} ===")
        df_trades = load_trades_csv(ticker)
        if df_trades.empty:
            print("  -> Skipping (no trades)")
            continue

        metrics = compute_ticker_metrics_from_df(ticker, df_trades)
        row = metrics_to_dict(metrics)
        rows.append(row)

        print(
            f"  trades={row['total_trades']}, "
            f"win_rate={row['win_rate']}%, "
            f"expectancy={row['expectancy_r']} R, "
            f"max_dd={row['max_drawdown_r']} R"
        )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.set_index("ticker").sort_values("expectancy_r", ascending=False)
    return df


def main():
    print("=== Week 8 — Sanity Check & Tuning ===")
    print("Reading trades from 'reports/{ticker}_trades.csv' ...")

    metrics_df = collect_ticker_metrics()

    if metrics_df.empty:
        print(
            "\nNo metrics computed. Make sure you've run:\n"
            "    python -m src.backtest_breakout\n"
            "first, so trades CSVs exist in 'reports/'."
        )
        return

    # Save full table
    REPORTS_DIR.mkdir(exist_ok=True)
    out_path = REPORTS_DIR / "week8_ticker_metrics.csv"
    metrics_df.to_csv(out_path)
    print(f"\nSaved per-ticker metrics to: {out_path}")

    # Print quick summary
    print("\nTop 3 tickers by expectancy (R per trade):")
    print(metrics_df.head(3)[["total_trades", "win_rate", "expectancy_r", "max_drawdown_r"]])

    print("\nBottom 3 tickers by expectancy:")
    print(metrics_df.tail(3)[["total_trades", "win_rate", "expectancy_r", "max_drawdown_r"]])

    print(
        "\nInterpretation tips:\n"
        " - Very negative expectancy (e.g. < -0.2 R) or win_rate < ~30% may be candidates to de-emphasize.\n"
        " - You can choose to:\n"
        "     * Drop those tickers from UNIVERSE in src/config.py, or\n"
        "     * Keep them but watch them carefully in future tuning.\n"
    )


if __name__ == "__main__":
    main()
