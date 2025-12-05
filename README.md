# Swing System

A quantitative breakout swing trading engine built in Python.

## Features

- Breakout trend-following strategy (EMA20/EMA50, 20-day highs)
- ATR-based stop and 2R target
- R-multiple and dollar P/L tracking
- Per-ticker backtests
- Portfolio backtests (multi-ticker, max-open constraint)
- Fully parameterized via `BreakoutParams` and `RiskConfig`

## Project Structure

- `src/config.py` – global parameters, universe, risk config  
- `src/fetch_history.py` / `src/update_data.py` – raw data download & refresh  
- `src/build_features.py` – build indicators & features into `data_processed/`  
- `src/signals/engine.py` – breakout signal logic (trend, breakout, volume, RSI, ATR)  
- `src/backtest/engine.py` – single-ticker backtest engine  
- `src/backtest_breakout.py` – runs backtests and saves trades/equity  
- `src/analysis/metrics.py` / `plots.py` / `analyze_backtests.py` – stats & charts  
- `src/portfolio_backtest.py` – multi-ticker portfolio metrics & equity curve  

## How to Run

```bash
# 1. Create and activate venv (once)
python -m venv .venv
.\.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt  # if you have one

# 3. Run single-ticker backtests
python -m src.backtest_breakout

# 4. Run portfolio backtest
python -m src.portfolio_backtest

# 5. Analyze per-ticker metrics
python -m src.analyze_backtests
