# src/run_weekly_watchlist.py

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPORTS_DIR = Path("reports")
TODAY_SIGNALS_PATH = REPORTS_DIR / "today_signals.csv"
WEEKLY_WATCHLIST_PATH = REPORTS_DIR / "weekly_watchlist.csv"

# Simple knobs you can tweak later
MIN_SCORE = 70.0
ALLOWED_GRADES = {"A", "B"}
MAX_ROWS = 20


def build_weekly_watchlist() -> None:
    print("=== Week 11 — Build Weekly Watchlist ===")

    if not TODAY_SIGNALS_PATH.exists() or TODAY_SIGNALS_PATH.stat().st_size == 0:
        print(f"[watchlist] No today_signals.csv found at {TODAY_SIGNALS_PATH}")
        if WEEKLY_WATCHLIST_PATH.exists():
            WEEKLY_WATCHLIST_PATH.unlink()
            print("[watchlist] Removed old weekly_watchlist.csv (no fresh signals).")
        return

    try:
        df = pd.read_csv(TODAY_SIGNALS_PATH)
    except Exception as e:
        print(f"[watchlist] ERROR reading today_signals.csv: {e}")
        return

    if df.empty:
        print("[watchlist] today_signals.csv is empty.")
        if WEEKLY_WATCHLIST_PATH.exists():
            WEEKLY_WATCHLIST_PATH.unlink()
            print("[watchlist] Removed old weekly_watchlist.csv (empty signals).")
        return

    # Ensure expected columns exist
    required_cols = ["ticker", "score", "setup", "entry", "stop", "target", "rr", "grade"]
    for col in required_cols:
        if col not in df.columns:
            print(f"[watchlist] Missing column '{col}' in today_signals.csv. Aborting.")
            return

    # Convert numeric columns
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df["rr"] = pd.to_numeric(df["rr"], errors="coerce")

    # Basic cleaning
    df = df[df["ticker"].notna() & (df["ticker"].astype(str).str.strip() != "")]
    df = df[df["score"].notna()]

    # Filters for "best" setups
    df = df[df["score"] >= MIN_SCORE]
    df = df[df["grade"].isin(ALLOWED_GRADES)]

    if df.empty:
        print("[watchlist] No signals passed MIN_SCORE / grade filters.")
        if WEEKLY_WATCHLIST_PATH.exists():
            WEEKLY_WATCHLIST_PATH.unlink()
            print("[watchlist] Removed old weekly_watchlist.csv (no qualifying setups).")
        return

    # Rank: A before B, then higher score, then higher RR
    grade_order = {"A": 0, "B": 1, "C": 2}
    df["__grade_order__"] = df["grade"].map(grade_order).fillna(99)

    df = df.sort_values(
        ["__grade_order__", "score", "rr"],
        ascending=[True, False, False],
    ).reset_index(drop=True)

    df = df.head(MAX_ROWS).copy()
    df = df.drop(columns=["__grade_order__"])

    WEEKLY_WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(WEEKLY_WATCHLIST_PATH, index=False)

    print(f"[watchlist] Saved {len(df)} rows to {WEEKLY_WATCHLIST_PATH.resolve()}")
    print("[watchlist] Done. Use the dashboard 'Watchlist' view to inspect them.")


if __name__ == "__main__":
    build_weekly_watchlist()
