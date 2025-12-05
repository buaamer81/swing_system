# Week 8 – Parameterization & Tuning Summary

Universe tested: AAPL, MSFT
Period: 2015–2026

AAPL:
- Trades: 50
- Win rate: 62.0%
- Expectancy: 0.552 R/trade
- Max DD: -5.39 R
- Avg holding: 8.8 days

MSFT:
- Trades: 49
- Win rate: 38.8%
- Expectancy: 0.066 R/trade
- Max DD: -13.54 R
- Avg holding: 7.8 days

Portfolio (AAPL + MSFT):
- Trades: 99
- Win rate: 50.5%
- Expectancy: 0.311 R/trade
- Profit factor: 1.70
- Max DD: -7.48 R
- Trades/year: ~9.2
- Hit target: 28.3%
- Hit stop: 44.4%

Changes made in Week 8:
- Introduced BreakoutParams/RiskConfig and made all signal + risk logic parameter-driven.
- Initially added strict filters → performance dropped (expectancy ~0.136 R).
- Relaxed filters:
  - min_price, min_avg_dollar_vol, min_atr → effectively off for now.
  - vol_multiple: 1.1 (lighter volume requirement).
  - RSI range widened to 40–90.

Conclusion:
- AAPL breakout system is strong and tradeable on its own.
- MSFT is marginal with small edge and deeper drawdowns.
- Portfolio (AAPL+MSFT) still positive, but AAPL is clearly the main driver.

Decision for v1:
- Official v1 universe: AAPL-only for live trading.
- Keep MSFT in code for future experiments / tuning.
