# src/backtest_breakout.py

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from src.config import UNIVERSE
from src.signals.engine import load_features
from src.backtest.engine import backtest_breakout_ticker


def save_equity_curve(ticker: str, series: pd.Series):
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    path = reports_dir / f"{ticker.lower()}_equity.png"

    plt.figure(figsize=(10, 4))
    series.plot(title=f"Equity Curve (R) — {ticker}")
    plt.xlabel("Date")
    plt.ylabel("Cumulative R")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

    print(f"Equity curve saved: {path}")


def save_trades_csv(ticker: str, trades):
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    rows = []
    for t in trades:
        rows.append({
            "ticker": t.ticker,
            "entry_date": t.entry_date,
            "exit_date": t.exit_date,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "stop_price": t.stop_price,
            "target_price": t.target_price,
            "risk_dollars": t.risk_dollars,
            "shares": t.shares,
            "dollar_pl": t.dollar_pl,
            "r_result": t.r_result,
            "holding_days": t.holding_days,
            "hit_target": t.hit_target,
            "hit_stop": t.hit_stop,
        })

    df = pd.DataFrame(rows)
    path = reports_dir / f"{ticker.lower()}_trades.csv"
    df.to_csv(path, index=False)
    print(f"Trades saved: {path}")


def main():
    print("=== Breakout Backtest (Week 5 spec) ===")

    # You can change these to whatever you want
    account_size = 1_000.0      # e.g. $1,000 starting notional
    risk_pct = 0.01             # 1% risk per trade
    max_hold_bars = 10          # max 10 bars holding

    for ticker in UNIVERSE:
        print(f"\n>>> Backtesting {ticker}...")
        df = load_features(ticker)

        result = backtest_breakout_ticker(
            ticker,
            df,
            account_size=account_size,
            risk_pct=risk_pct,
            max_hold_bars=max_hold_bars,
        )

        print(f"Trades: {result.total_trades}")
        print(f"Win rate: {result.win_rate:.1f}%")
        print(f"Expectancy: {result.expectancy_r:.3f} R per trade")
        print(f"Total P/L: {result.total_pl_dollars:.2f} $ (non-compounded)")
        print(f"Max drawdown: {result.max_drawdown_r:.2f} R")
        print(f"Avg holding: {result.avg_holding:.1f} days")

        if not result.equity_curve_r.empty:
            save_equity_curve(ticker, result.equity_curve_r)

        save_trades_csv(ticker, result.trades)


if __name__ == "__main__":
    main()
