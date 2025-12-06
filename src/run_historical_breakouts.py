# src/run_historical_breakouts.py

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from src.config import UNIVERSE, BREAKOUT_PARAMS
from src.signals.engine import load_features, _breakout_signal_from_row, Signal

OUTPUT_PATH = Path("reports/historical_signals.csv")


def _grade_from_score(score: float) -> str:
    """Simple grading based on score."""
    if pd.isna(score):
        return "C"
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    return "C"


def collect_signals_for_ticker(
    ticker: str,
    max_signals: int = 200,
) -> List[Signal]:
    """
    Scan the full history for a single ticker and collect breakout signals.

    max_signals: safety cap per ticker so the file doesn't explode in size.
    """
    df = load_features(ticker)
    signals: List[Signal] = []

    for _, row in df.iterrows():
        sig = _breakout_signal_from_row(ticker, row, BREAKOUT_PARAMS)
        if sig is not None:
            signals.append(sig)
            if len(signals) >= max_signals:
                break

    return signals


def run_historical() -> None:
    """
    Scan all tickers in UNIVERSE and write historical breakout signals to CSV.

    Output schema:
        ticker, date, score, setup, entry, stop, target, rr, grade
    """
    rows: list[dict] = []

    for ticker in UNIVERSE:
        print(f"[hist] Scanning {ticker}...")
        try:
            sigs = collect_signals_for_ticker(ticker)
        except Exception as e:
            print(f"[hist] ERROR for {ticker}: {e}")
            continue

        for sig in sigs:
            rows.append(
                {
                    "ticker": sig.ticker,
                    "date": sig.date,
                    "score": float(sig.score),
                    "setup": sig.setup or "Breakout",
                    "entry": float(sig.entry),
                    "stop": float(sig.stop),
                    "target": float(sig.target),
                    "rr": float(sig.r_multiple),
                    "grade": _grade_from_score(float(sig.score)),
                }
            )

    df = pd.DataFrame(rows)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if df.empty:
        if OUTPUT_PATH.exists():
            OUTPUT_PATH.unlink()
        print("[hist] No historical signals found. Removed historical_signals.csv if it existed.")
        return

    # Sort by date (newest first) then score (highest first)
    df = df.sort_values(["date", "score"], ascending=[False, False]).reset_index(drop=True)

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"[hist] Saved {len(df)} historical signals to {OUTPUT_PATH.resolve()}")


if __name__ == "__main__":
    run_historical()
