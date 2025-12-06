from __future__ import annotations

from pathlib import Path
import pandas as pd


REPORTS_DIR = Path("reports")
TODAY_SIGNALS_PATH = REPORTS_DIR / "today_signals.csv"
HISTORICAL_SIGNALS_PATH = REPORTS_DIR / "historical_signals.csv"
WEEKLY_WATCHLIST_PATH = REPORTS_DIR / "weekly_watchlist.csv"

def _demo_signals() -> pd.DataFrame:
    """
    Fallback demo data so the dashboard always shows something even
    if you haven't generated today's signals yet.
    """
    data = [
        {
            "ticker": "AAPL",
            "score": 84,
            "setup": "Breakout",
            "entry": 190.5,
            "stop": 185.0,
            "target": 201.5,
            "rr": 2.2,
            "grade": "A",
        },
        {
            "ticker": "MSFT",
            "score": 76,
            "setup": "Breakout",
            "entry": 415.2,
            "stop": 404.0,
            "target": 438.0,
            "rr": 2.0,
            "grade": "B",
        },
    ]
    return pd.DataFrame(data)


def _sanitize_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure the DataFrame has the expected columns and types
    for 'today' signals (no date column).
    """
    required_cols = [
        "ticker",
        "score",
        "setup",
        "entry",
        "stop",
        "target",
        "rr",
        "grade",
    ]

    for col in required_cols:
        if col not in df.columns:
            if col in ("ticker", "setup", "grade"):
                df[col] = ""
            else:
                df[col] = pd.NA

    df = df[required_cols]

    df["ticker"] = df["ticker"].astype(str)
    df["setup"] = df["setup"].astype(str)
    df["grade"] = df["grade"].astype(str)

    numeric_cols = ["score", "entry", "stop", "target", "rr"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df[df["ticker"].notna() & (df["ticker"].str.strip() != "")]

    df = (
        df.sort_values(["ticker", "score"], ascending=[True, False])
          .drop_duplicates(subset=["ticker"], keep="first")
          .reset_index(drop=True)
    )
    return df


def _sanitize_signals_with_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sanitize historical signals (includes a 'date' column).
    """
    required_cols = [
        "ticker",
        "date",
        "score",
        "setup",
        "entry",
        "stop",
        "target",
        "rr",
        "grade",
    ]

    for col in required_cols:
        if col not in df.columns:
            if col in ("ticker", "setup", "grade"):
                df[col] = ""
            elif col == "date":
                df[col] = pd.NaT
            else:
                df[col] = pd.NA

    df = df[required_cols]

    df["ticker"] = df["ticker"].astype(str)
    df["setup"] = df["setup"].astype(str)
    df["grade"] = df["grade"].astype(str)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    numeric_cols = ["score", "entry", "stop", "target", "rr"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df[df["ticker"].notna() & (df["ticker"].str.strip() != "")]
    df = df[df["date"].notna()]

    df = df.sort_values(["date", "score"], ascending=[False, False]).reset_index(drop=True)
    return df


def load_today_signals(allow_demo: bool = True) -> pd.DataFrame:
    """
    Load today's signals from CSV.

    - If file missing/empty/corrupted -> demo or empty.
    """
    signals_path = TODAY_SIGNALS_PATH

    if signals_path.exists() and signals_path.stat().st_size == 0:
        print("[load_today_signals] Removing empty CSV file...")
        signals_path.unlink()

    if not signals_path.exists():
        return _demo_signals() if allow_demo else pd.DataFrame()

    try:
        df = pd.read_csv(signals_path)
    except Exception as e:
        print(f"[load_today_signals] Error reading CSV: {e}")
        return _demo_signals() if allow_demo else pd.DataFrame()

    if df.empty:
        return _demo_signals() if allow_demo else df

    return _sanitize_signals(df)


def load_historical_signals() -> pd.DataFrame:
    """
    Load historical breakout signals from CSV.

    - If file missing/empty/corrupted -> return empty DataFrame.
    """
    signals_path = HISTORICAL_SIGNALS_PATH

    if not signals_path.exists() or signals_path.stat().st_size == 0:
        print("[load_historical_signals] No historical_signals.csv found yet.")
        return pd.DataFrame()

    try:
        df = pd.read_csv(signals_path)
    except Exception as e:
        print(f"[load_historical_signals] Error reading CSV: {e}")
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    return _sanitize_signals_with_date(df)

def load_weekly_watchlist() -> pd.DataFrame:
    """
    Load the weekly watchlist from CSV.

    - If file missing/empty/corrupted -> return empty DataFrame.
    - Schema is the same as today's signals (no date column).
    """
    signals_path = WEEKLY_WATCHLIST_PATH

    if not signals_path.exists() or signals_path.stat().st_size == 0:
        print("[load_weekly_watchlist] No weekly_watchlist.csv found yet.")
        return pd.DataFrame()

    try:
        df = pd.read_csv(signals_path)
    except Exception as e:
        print(f"[load_weekly_watchlist] Error reading CSV: {e}")
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    # Reuse today-signals sanitizer (same columns)
    return _sanitize_signals(df)