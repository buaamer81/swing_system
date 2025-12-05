# src/signals/features.py

from pathlib import Path
import pandas as pd

from src.config import DATA_DIR_RAW, DATA_DIR_PROCESSED, UNIVERSE
from src.data.prices import load_existing_data
from src.signals.indicators import (
    ema,
    rsi,
    atr,
    rolling_high,
    rolling_low,
    sma,
    avg_volume,
)


PROCESSED_DIR = Path(DATA_DIR_PROCESSED)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a price DataFrame with columns: Open, High, Low, Close, Adj Close, Volume
    add swing-trading indicators and return the expanded DataFrame.
    """

    # Ensure required columns exist
    required_cols = {"Open", "High", "Low", "Close", "Volume"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in input DataFrame: {missing}")

    # 🔹 Coerce core price columns to numeric (in case they came in as strings)
    numeric_cols = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows where any core columns are completely invalid
    df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"])

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # Trend / moving averages
    df["EMA20"] = ema(close, 20)
    df["EMA50"] = ema(close, 50)
    df["SMA200"] = sma(close, 200)

    # Momentum
    df["RSI10"] = rsi(close, 10)
    df["RSI14"] = rsi(close, 14)

    # Volatility
    df["ATR14"] = atr(high, low, close, 14)

    # Breakout levels
    df["HIGH_10"] = rolling_high(high, 10)
    df["HIGH_20"] = rolling_high(high, 20)
    df["LOW_10"] = rolling_low(low, 10)
    df["LOW_20"] = rolling_low(low, 20)

    # Volume
    df["VOL_AVG20"] = avg_volume(volume, 20)
    df["VOL_AVG50"] = avg_volume(volume, 50)

    # Returns
    df["RET_1D"] = close.pct_change(1)
    df["RET_5D"] = close.pct_change(5)

    return df


def build_features_for_ticker(ticker: str, save: bool = True) -> pd.DataFrame:
    """
    Load raw price data for a ticker, compute indicators,
    and optionally save to data_processed/{TICKER}.parquet.
    """
    print(f"[FEATURES] Building features for {ticker}...")

    df = load_existing_data(ticker)
    if df is None or df.empty:
        raise ValueError(f"No raw data available for {ticker}. "
                         f"Make sure you ran fetch_history first.")

    df_feat = add_indicators(df.copy())

    if save:
        out_path = PROCESSED_DIR / f"{ticker.upper()}.csv"
        df_feat.to_csv(out_path)
        print(f"[FEATURES] Saved features for {ticker} to {out_path}")

    return df_feat


def build_features_for_universe(save: bool = True):
    """
    Build features for all tickers in UNIVERSE.
    """
    print("=== Building features for all tickers ===")
    for ticker in UNIVERSE:
        try:
            build_features_for_ticker(ticker, save=save)
        except Exception as e:
            print(f"[ERROR] Failed to build features for {ticker}: {e}")
    print("=== Done building features ===")
