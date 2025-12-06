# src/config.py
from dataclasses import dataclass

# ====== Breakout signal configuration ======

@dataclass
class BreakoutParams:
    # --- Signal logic ---
    breakout_lookback: int = 20      # HIGH_20 breakouts
    breakout_buffer: float = 0.99    # more permissive: close >= HIGH_20 * 0.99

    ema_fast: int = 20
    ema_slow: int = 50

    rsi_length: int = 10
    # wider RSI window so more candidates pass
    rsi_min: float = 35.0
    rsi_max: float = 90.0

    vol_lookback: int = 20
    # softer volume requirement for testing
    vol_multiple: float = 1.0        # Volume > 1.0 * VOL_AVG20

    # --- Risk / exits ---
    stop_atr_mult: float = 1.5       # stop = close - 1.5 * ATR14
    target_r: float = 2.0            # 2R target

    # --- Extra filters (Week 8) ---
    # keep some basic sanity but still relaxed
    min_price: float = 5.0           # allow cheaper stocks but avoid penny junk
    min_avg_dollar_vol: float = 1_000_000.0  # $1M avg dollar volume
    min_atr: float = 0.1             # avoid totally dead names


BREAKOUT_PARAMS = BreakoutParams()

# Your current small test universe
UNIVERSE = ["AAPL", "MSFT", "TSLA", "NVDA", "META", "GOOGL", "AMZN", "NFLX"]  # you can add more later


# ====== Risk / position sizing config ======

@dataclass
class RiskConfig:
    account_size: float = 10_000.0
    risk_pct: float = 0.01
    max_hold_bars: int = 10


RISK_CONFIG = RiskConfig()

# ====== Data paths ======

DATA_DIR_RAW = "data_raw"
DATA_DIR_PROCESSED = "data_processed"

# How far back you want history
HISTORY_START_DATE = "2015-01-01"  # adjust if you want more/less history
