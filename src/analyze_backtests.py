# src/analyze_backtests.py

from pathlib import Path

import pandas as pd

from src.config import UNIVERSE
from src.analysis.metrics import compute_ticker_metrics_from_df, metrics_to_dict
from src.analysis.plots import (
    plot_equity_curve_r,
    plot_drawdown_curve,
    plot_r_distribution,
    plot_r_scatter,
)


def load_trades_csv(ticker: str) -> pd.DataFrame:
    reports_dir = Path("reports")
    path = reports_dir / f"{ticker.lower()}_trades.csv"
    if not path.exists():
        print(f"[WARN] Trades file not found for {ticker}: {path}")
        return pd.DataFrame()

    df = pd.read_csv(path)
    # parse dates
    for col in ("entry_date", "exit_date"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    return df


def analyze_ticker(ticker: str):
    print(f"\n=== Week 6 Analysis for {ticker} ===")

    df_trades = load_trades_csv(ticker)
    if df_trades.empty:
        print("No trades found.")
        return

    # 1) Metrics
    metrics = compute_ticker_metrics_from_df(ticker, df_trades)
    m_dict = metrics_to_dict(metrics)

    for k, v in m_dict.items():
        print(f"{k:18}: {v}")

    # 2) Plots
    eq_path = plot_equity_curve_r(ticker, df_trades)
    dd_path = plot_drawdown_curve(ticker, df_trades)
    dist_path = plot_r_distribution(ticker, df_trades)
    scatter_path = plot_r_scatter(ticker, df_trades)

    print("\nSaved plots:")
    if eq_path:
        print(f"  Equity curve (R):      {eq_path}")
    if dd_path:
        print(f"  Drawdown curve (R):    {dd_path}")
    if dist_path:
        print(f"  R distribution:        {dist_path}")
    if scatter_path:
        print(f"  R per trade scatter:   {scatter_path}")


def main():
    print("=== Week 6 — Metrics & Summaries ===")

    for ticker in UNIVERSE:
        analyze_ticker(ticker)


if __name__ == "__main__":
    main()
