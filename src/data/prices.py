# src/data/prices.py

from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from src.config import DATA_DIR_RAW, UNIVERSE, HISTORY_START_DATE


# Ensure the raw data directory exists
RAW_DIR = Path(DATA_DIR_RAW)
RAW_DIR.mkdir(parents=True, exist_ok=True)


def get_ticker_path(ticker: str) -> Path:
    """Return the CSV path for a given ticker in data_raw/."""
    filename = f"{ticker.upper()}.csv"
    return RAW_DIR / filename


def fetch_history_for_ticker(ticker: str,
                             start: str = HISTORY_START_DATE,
                             end: str | None = None) -> pd.DataFrame | None:
    """
    Download historical OHLCV data for a single ticker using yfinance
    and save it to data_raw/{TICKER}.csv.
    """
    print(f"[HISTORY] Fetching {ticker} from {start} to {end or 'latest'}...")

    df = yf.download(ticker, start=start, end=end, progress=False)

    if df.empty:
        print(f"[HISTORY] No data returned for {ticker}.")
        return None

    # yfinance returns Date index, keep it and store as CSV
    path = get_ticker_path(ticker)
    df.to_csv(path)
    print(f"[HISTORY] Saved {len(df)} rows to {path}")

    return df


def fetch_all_history():
    """
    Download full history for all tickers in UNIVERSE.
    Overwrites any existing files.
    """
    print("=== Fetching full history for all tickers ===")
    for ticker in UNIVERSE:
        try:
            fetch_history_for_ticker(ticker)
        except Exception as e:
            print(f"[ERROR] Failed to fetch {ticker}: {e}")
    print("=== Done fetching history ===")


def load_existing_data(ticker: str) -> pd.DataFrame | None:
    """
    Load existing CSV for a ticker, or None if file doesn't exist.
    Ensure the index is a proper DatetimeIndex.
    """
    path = get_ticker_path(ticker)
    if not path.exists():
        return None

    # Read CSV: use first column as index, no parse_dates here
    df = pd.read_csv(path, index_col=0)

    # Force the index to be datetime
    df.index = pd.to_datetime(df.index, errors="coerce")
    df.index.name = "Date"

    # Drop any rows where the date could not be parsed (e.g. 'Ticker' or header junk)
    df = df[~df.index.isna()]

    return df



def update_ticker_data(ticker: str):
    """
    Update existing ticker data file with new rows since last saved date.
    If no file exists, fetch full history from HISTORY_START_DATE.
    """
    print(f"[UPDATE] Updating data for {ticker}...")

    df_existing = load_existing_data(ticker)

    if df_existing is None or df_existing.empty:
        print(f"[UPDATE] No existing data for {ticker}, fetching full history...")
        return fetch_history_for_ticker(ticker)

    last_timestamp = df_existing.index.max()
    last_timestamp = pd.to_datetime(last_timestamp)
    print(f"[UPDATE] Last timestamp in file: {last_timestamp}")

    # Compute the next day after the last timestamp
    start_next = last_timestamp + timedelta(days=1)

    # If start_next is today or in the future, there is nothing new to fetch
    today = datetime.utcnow().date()
    if start_next.date() >= today:
        print(f"[UPDATE] No new market data yet for {ticker} (up to date).")
        return df_existing

    start_str = start_next.strftime("%Y-%m-%d")
    print(f"[UPDATE] Fetching new data from {start_str} onward...")

    df_new = yf.download(
        ticker,
        start=start_str,
        progress=False,
    )

    if df_new.empty:
        print(f"[UPDATE] No new data returned for {ticker}.")
        return df_existing

    df_updated = pd.concat([df_existing, df_new])
    df_updated = df_updated[~df_updated.index.duplicated(keep="last")]

    path = get_ticker_path(ticker)
    df_updated.to_csv(path)
    print(f"[UPDATE] {ticker}: added {len(df_new)} new rows, total {len(df_updated)} rows in {path}")

    return df_updated


def update_all_data():
    """
    Update data for all tickers in UNIVERSE.
    """
    print("=== Updating data for all tickers ===")
    for ticker in UNIVERSE:
        try:
            update_ticker_data(ticker)
        except Exception as e:
            print(f"[ERROR] Failed to update {ticker}: {e}")
    print("=== Done updating data ===")
