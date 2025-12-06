from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
import mplfinance as mpf


DATA_PROCESSED_DIR = Path("data_processed")


def _load_price_data(ticker: str) -> pd.DataFrame:
    """
    Load processed OHLCV+indicator data for a ticker.

    Expects a CSV in data_processed/{TICKER}.csv with at least:
    Date, Open, High, Low, Close, Volume, EMA20, EMA50
    """
    csv_path = DATA_PROCESSED_DIR / f"{ticker}.csv"
    if not csv_path.exists():
        return pd.DataFrame()

    df = pd.read_csv(csv_path)

    if "Date" not in df.columns:
        return pd.DataFrame()

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df = df.set_index("Date").sort_index()

    # Ensure OHLCV exist
    required = ["Open", "High", "Low", "Close", "Volume"]
    for col in required:
        if col not in df.columns:
            return pd.DataFrame()

    return df


def get_price_slice(
    ticker: str,
    as_of: Optional[pd.Timestamp],
    lookback: int = 90,
) -> pd.DataFrame:
    """
    Return a slice of price data up to `as_of` (or latest bar if None),
    limited to the last `lookback` bars.
    """
    df = _load_price_data(ticker)
    if df.empty:
        return df

    if as_of is not None:
        as_of = pd.to_datetime(as_of).normalize()
        df = df[df.index <= as_of]

    return df.tail(lookback)


def plot_signal_chart(
    ticker: str,
    signal_row: pd.Series,
    view_mode: str = "Today",
    lookback: int = 90,
):
    """
    Build a simple candlestick chart with EMAs + entry/stop/target lines.

    Returns a Matplotlib Figure, or None if data is missing.
    """
    # Historical: use signal date as "as_of"
    if (
        view_mode == "Historical"
        and "date" in signal_row.index
        and pd.notna(signal_row["date"])
    ):
        as_of = pd.to_datetime(signal_row["date"]).normalize()
    else:
        # Today mode: just use the latest available bar
        as_of = None

    prices = get_price_slice(ticker, as_of=as_of, lookback=lookback)
    if prices.empty:
        return None

    add_plots = []

    # EMA20 / EMA50 if present in processed data
    for ema_col in ["EMA20", "EMA50"]:
        if ema_col in prices.columns:
            add_plots.append(
                mpf.make_addplot(prices[ema_col], width=1.0)
            )

    # Horizontal levels: entry, stop, target with clear colors
    idx = prices.index
    level_colors = {
        "entry": "tab:blue",   # entry  → blue dashed
        "stop": "tab:red",     # stop   → red dashed
        "target": "tab:green", # target → green dashed
    }

    for col in ["entry", "stop", "target"]:
        if col in signal_row.index and pd.notna(signal_row[col]):
            try:
                value = float(signal_row[col])
            except (TypeError, ValueError):
                continue

            level_series = pd.Series(value, index=idx)
            add_plots.append(
                mpf.make_addplot(
                    level_series,
                    linestyle="--",
                    width=0.8,
                    color=level_colors.get(col, "k"),
                )
            )

    # Candlestick + volume + overlays
    fig, _ = mpf.plot(
        prices[["Open", "High", "Low", "Close", "Volume"]],
        type="candle",
        volume=True,
        addplot=add_plots if add_plots else None,
        returnfig=True,
        figsize=(9, 5),    # smaller, cleaner
    )

    # Title with basic info
    title_bits = [ticker]

    if "setup" in signal_row.index:
        title_bits.append(str(signal_row["setup"]))

    if "grade" in signal_row.index:
        title_bits.append(f"grade {signal_row['grade']}")

    if "score" in signal_row.index and pd.notna(signal_row["score"]):
        try:
            title_bits.append(f"score {float(signal_row['score']):.1f}")
        except (TypeError, ValueError):
            pass

    fig.suptitle(" · ".join(title_bits))

    return fig
