# src/signals/indicators.py

import pandas as pd
import numpy as np


def ema(series: pd.Series, length: int) -> pd.Series:
    """
    Exponential Moving Average
    """
    return series.ewm(span=length, adjust=False).mean()


def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    """
    Relative Strength Index (RSI)
    Classic Wilder RSI implementation.
    """
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=length, min_periods=length).mean()
    avg_loss = loss.rolling(window=length, min_periods=length).mean()

    # After initial window, use Wilder's smoothing
    avg_gain = avg_gain.combine_first(
        gain.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
    )
    avg_loss = avg_loss.combine_first(
        loss.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
    )

    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """
    True Range component for ATR.
    """
    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr


def atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    """
    Average True Range
    """
    tr = true_range(high, low, close)
    return tr.rolling(window=length, min_periods=length).mean()


def rolling_high(series: pd.Series, window: int) -> pd.Series:
    """
    Rolling highest high over a given window.
    """
    return series.rolling(window=window, min_periods=window).max()


def rolling_low(series: pd.Series, window: int) -> pd.Series:
    """
    Rolling lowest low over a given window.
    """
    return series.rolling(window=window, min_periods=window).min()


def sma(series: pd.Series, length: int) -> pd.Series:
    """
    Simple Moving Average
    """
    return series.rolling(window=length, min_periods=length).mean()


def avg_volume(volume: pd.Series, length: int = 20) -> pd.Series:
    """
    Rolling average volume
    """
    return volume.rolling(window=length, min_periods=length).mean()
