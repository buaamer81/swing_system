# src/signals/engine.py

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd

from src.config import DATA_DIR_PROCESSED, UNIVERSE, BREAKOUT_PARAMS, BreakoutParams

PROCESSED_DIR = Path(DATA_DIR_PROCESSED)


@dataclass
class Signal:
    """Represents one breakout setup on a single bar.

    This is used both by the live scanner (scan_signals.py) and by the
    backtest engine when it turns historical rows into trades.
    """
    ticker: str
    setup: str
    score: float

    date: pd.Timestamp
    close: float
    entry: float
    stop: float
    target: float
    r_multiple: float

    atr: float
    rsi: float
    volume: float

    notes: str = ""


def load_features(ticker: str) -> pd.DataFrame:
    """Load processed feature data for a ticker.

    Expects CSVs like data_processed/AAPL.csv with columns:
    Date, Open, High, Low, Close, Volume, EMA20, EMA50, RSI10, ATR14,
    HIGH_20, VOL_AVG20, etc.
    """
    path = PROCESSED_DIR / f"{ticker}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Processed features not found for {ticker}: {path}")
    df = pd.read_csv(path)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
    return df


def _breakout_signal_from_row(
    ticker: str,
    row: pd.Series,
    params: Optional[BreakoutParams] = None,
) -> Optional[Signal]:
    """Core breakout logic for a single bar.

    Applies trend, breakout, volume, RSI, and basic liquidity filters.
    Returns a Signal if all conditions pass, otherwise None.
    """
    if params is None:
        params = BREAKOUT_PARAMS

    # Required columns
    required_cols = [
        "Close", "Open", "High", "Low", "Volume",
        "EMA20", "EMA50",
        "HIGH_20",
        "VOL_AVG20",
        "RSI10", "ATR14",
    ]
    for col in required_cols:
        if col not in row:
            return None

    close = float(row["Close"])
    open_ = float(row["Open"])
    high = float(row["High"])
    low = float(row["Low"])
    volume = float(row["Volume"])

    ema_fast = float(row["EMA20"])
    ema_slow = float(row["EMA50"])
    high_n = float(row["HIGH_20"])
    vol_avg = float(row["VOL_AVG20"])
    rsi = float(row["RSI10"])
    atr = float(row["ATR14"])

    # Basic NaN / inf safety
    vals = [close, open_, high, low, volume, ema_fast, ema_slow, high_n, vol_avg, rsi, atr]
    if any((not np.isfinite(v) for v in vals)):
        return None

    # ---------- Extra Week 8 filters ----------

    # Minimum price
    if close < params.min_price:
        return None

    # Minimum average dollar volume
    dollar_vol = vol_avg * close
    if dollar_vol < params.min_avg_dollar_vol:
        return None

    # Minimum ATR (avoid ultra-dead symbols)
    if atr < params.min_atr:
        return None

    # ---------- Trend filter: price above both EMAs and fast > slow ----------
    if not (close > ema_fast > ema_slow):
        return None

    # ---------- Breakout filter: near or above recent high ----------
    breakout_level = high_n * params.breakout_buffer
    if not (close >= breakout_level):
        return None

    # ---------- Volume filter: current volume above avg * multiple ----------
    if not (volume > params.vol_multiple * vol_avg):
        return None

    # ---------- RSI filter ----------
    if not (params.rsi_min <= rsi <= params.rsi_max):
        return None

    # ---------- Risk / reward levels ----------
    risk_per_share = params.stop_atr_mult * atr
    if risk_per_share <= 0:
        return None

    entry = close
    stop = entry - risk_per_share
    target = entry + params.target_r * risk_per_share

    # ---------- Scoring: breakout strength & volume surge ----------
    breakout_score = (close - high_n) / max(atr, 1e-6)
    vol_score = (volume / max(vol_avg, 1.0)) - 1.0

    raw_score = 50.0 + 25.0 * breakout_score + 25.0 * vol_score
    score = float(max(0.0, min(100.0, raw_score)))

    notes_parts = [
        f"breakout_score={breakout_score:.2f}",
        f"vol_score={vol_score:.2f}",
        f"dollar_vol={dollar_vol/1_000_000:.1f}M",
    ]
    notes = "; ".join(notes_parts)

    date = row["Date"] if "Date" in row.index else None
    if pd.isna(date):
        date = None

    return Signal(
        ticker=ticker,
        setup="Breakout",
        score=score,
        date=pd.to_datetime(date) if date is not None else pd.NaT,
        close=close,
        entry=entry,
        stop=stop,
        target=target,
        r_multiple=params.target_r,
        atr=atr,
        rsi=rsi,
        volume=volume,
        notes=notes,
    )


def generate_signals_for_ticker(ticker: str) -> List[Signal]:
    """Generate breakout signals for the *latest* bar of a ticker.

    This is used by the real-time scanner (scan_signals.py).
    """
    df = load_features(ticker)
    if df.empty:
        return []

    last_row = df.iloc[-1]
    sig = _breakout_signal_from_row(ticker, last_row)
    return [sig] if sig is not None else []


def scan_universe(universe: Optional[List[str]] = None) -> List[Signal]:
    """Scan all tickers in the universe and return a ranked list of Signals."""
    if universe is None:
        universe = UNIVERSE

    all_signals: List[Signal] = []

    print("=== Scanning universe for signals ===")
    for ticker in universe:
        try:
            signals = generate_signals_for_ticker(ticker)
            all_signals.extend(signals)
        except Exception as e:
            print(f"[ERROR] Failed to generate signals for {ticker}: {e}")

    # Sort by score descending (best first)
    all_signals.sort(key=lambda s: s.score, reverse=True)
    return all_signals
