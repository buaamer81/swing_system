# src/config.py
from dataclasses import dataclass
# Which tickers you want in your personal universe
@dataclass
class BreakoutParams:
    # --- Signal logic ---
    breakout_lookback: int = 20      # HIGH_20 breakouts
    breakout_buffer: float = 0.995   # close >= high_20 * buffer

    ema_fast: int = 20
    ema_slow: int = 50

    rsi_length: int = 10
    rsi_min: float = 40.0
    rsi_max: float = 90.0

    vol_lookback: int = 20
    vol_multiple: float = 1.1        # Volume > vol_multiple * VOL_AVG20

    # --- Risk / exits ---
    stop_atr_mult: float = 1.5       # stop = close - 1.5 * ATR14
    target_r: float = 2.0            # 2R target

    # --- Extra filters (Week 8) ---
    min_price: float = 0.0
    min_avg_dollar_vol: float = 0.0  # $5M avg dollar volume
    min_atr: float = 0.0

BREAKOUT_PARAMS = BreakoutParams()

UNIVERSE = ["AAPL", "MSFT"]  # you can add more later

@dataclass
class RiskConfig:
    account_size: float = 10_000.0
    risk_pct: float = 0.01
    max_hold_bars: int = 10


RISK_CONFIG = RiskConfig()

# Where to store data
DATA_DIR_RAW = "data_raw"
DATA_DIR_PROCESSED = "data_processed"

# How far back you want history
HISTORY_START_DATE = "2015-01-01"  # adjust if you want more/less history
