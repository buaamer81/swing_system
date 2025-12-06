# src/run_today_signals.py

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from src.config import UNIVERSE
from src.signals.engine import (
    generate_signals_for_ticker,
    Signal,
    load_features,
)

OUTPUT_PATH = Path("reports/today_signals.csv")

# Toggle: if True, build simple test signals from latest bar
# when there are no strict breakout signals.
USE_FALLBACK_FROM_LATEST_BAR = True


def _compute_rr(entry: float, stop: float, target: float) -> float:
    """
    Compute Risk/Reward ratio if not already given.
    R = entry - stop
    Reward = target - entry
    rr = Reward / R
    """
    if entry is None or stop is None or target is None:
        return float("nan")
    risk = entry - stop
    if risk <= 0:
        return float("nan")
    reward = target - entry
    return reward / risk


def _grade_from_score(score: float) -> str:
    """
    Simple grading scheme based on score.
    You can refine this later.
    """
    if pd.isna(score):
        return "C"
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    return "C"


def _signals_for_ticker(ticker: str) -> List[Signal]:
    """
    Wrapper around generate_signals_for_ticker with error handling.
    Your engine currently returns a List[Signal] (0 or 1 element).
    """
    try:
        signals = generate_signals_for_ticker(ticker)
        if signals is None:
            return []
        return signals
    except Exception as e:
        print(f"[run_today] ERROR generating signals for {ticker}: {e}")
        return []


def _fallback_rows_from_latest_bar() -> list[dict]:
    """
    Build simple 'test' signals from the latest bar of each ticker
    using real market data (Close, ATR, etc.), even if they are not
    strict breakouts. This is only for development / dashboard testing.
    """
    rows: list[dict] = []

    for ticker in UNIVERSE:
        try:
            df = load_features(ticker)
        except Exception as e:
            print(f"[run_today] Fallback: failed to load features for {ticker}: {e}")
            continue

        if df.empty:
            continue

        last = df.iloc[-1]

        close = float(last.get("Close"))
        atr = float(last.get("ATR14", abs(close) * 0.02))  # rough fallback
        if not pd.notna(atr) or atr <= 0:
            atr = max(abs(close) * 0.02, 0.5)

        entry = close
        stop = entry - 1.5 * atr
        target = entry + 3.0 * atr  # ~2R
        rr = _compute_rr(entry, stop, target)

        # Simple score based on trend-ish behaviour & volatility
        ema_fast = float(last.get("EMA20", close))
        ema_slow = float(last.get("EMA50", close))
        trend_score = 10.0 if ema_fast > ema_slow else 0.0
        vol_score = min(40.0, 40.0 * (atr / max(1.0, close * 0.01)))
        base_score = 60.0

        score = max(0.0, min(100.0, base_score + trend_score + vol_score))
        grade = _grade_from_score(score)

        rows.append(
            {
                "ticker": ticker,
                "score": score,
                "setup": "Test",  # distinguish from real "Breakout"
                "entry": entry,
                "stop": stop,
                "target": target,
                "rr": rr,
                "grade": grade,
            }
        )

    return rows


def run_today() -> None:
    """
    Primary path: use strict breakout engine.
    If no signals are produced and USE_FALLBACK_FROM_LATEST_BAR is True,
    generate simple test signals from latest bars for dashboard testing.
    """
    rows: list[dict] = []

    # ---------- 1) Strict breakout signals ----------
    for ticker in UNIVERSE:
        print(f"[run_today] Processing {ticker}...")
        signals = _signals_for_ticker(ticker)
        if not signals:
            continue

        # Your generate_signals_for_ticker currently returns at most ONE Signal,
        # but we write this defensively: take the highest-score one if there are several.
        signals_sorted = sorted(signals, key=lambda s: s.score, reverse=True)
        sig: Signal = signals_sorted[0]

        entry = float(sig.entry)
        stop = float(sig.stop)
        target = float(sig.target)
        score = float(sig.score)
        setup = sig.setup or "Breakout"
        rr = float(sig.r_multiple) if sig.r_multiple is not None else float("nan")

        if pd.isna(rr):
            rr = _compute_rr(entry, stop, target)

        grade = _grade_from_score(score)

        rows.append(
            {
                "ticker": sig.ticker,
                "score": score,
                "setup": setup,
                "entry": entry,
                "stop": stop,
                "target": target,
                "rr": rr,
                "grade": grade,
            }
        )

    # ---------- 2) If none, build fallback test signals ----------
    if not rows and USE_FALLBACK_FROM_LATEST_BAR:
        print("[run_today] No breakout signals found. Building fallback test signals from latest bars...")
        rows = _fallback_rows_from_latest_bar()

    df = pd.DataFrame(rows)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if df.empty:
        if OUTPUT_PATH.exists():
            OUTPUT_PATH.unlink()
        print("[run_today] No signals (even fallback). Removed today_signals.csv if it existed.")
        return

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"[run_today] Saved {len(df)} signals to {OUTPUT_PATH.resolve()}")


if __name__ == "__main__":
    run_today()
