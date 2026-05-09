Title: BTC Momentum Backtest — MA Crossover Strategy

---

Project Overview

A Python-based backtest of a simple MA20/MA200 crossover momentum strategy on BTC/USDT, using Binance daily candlestick data (Aug 2023 → May 2026, 1000 candles).

Data Source: Binance Public API (api.binance.com) — no account or API key required.

---

Strategy Logic

MA20 > MA200

• Condition: MA20 > MA200

• Position: Long (+1)

MA20 < MA200

• Condition: MA20 < MA200

• Position: Short (-1)

Entry/exit triggered on daily MA crossover — no stop-loss or position sizing.

---

Backtest Results (801 days, Feb 2024 → May 2026)

Total return

• Metric: Total return

• MA Crossover Strategy: +2.38%

• BTC Buy & Hold: +31.50%

Annualized return

• Metric: Annualized return

• MA Crossover Strategy: +1.08%

• BTC Buy & Hold: +13.29%

Max drawdown

• Metric: Max drawdown

• MA Crossover Strategy: -35.32%

• BTC Buy & Hold: -49.53%

Win rate

• Metric: Win rate

• MA Crossover Strategy: 49.3%

• BTC Buy & Hold: —

Trades (5 total):

2024-08-13

• Date: 2024-08-13

• Action: SELL (close short)

• Price: $60,587

2024-10-18

• Date: 2024-10-18

• Action: BUY

• Price: $68,428

2025-03-22

• Date: 2025-03-22

• Action: SELL

• Price: $83,840

2025-05-02

• Date: 2025-05-02

• Action: BUY

• Price: $96,887

2025-11-04

• Date: 2025-11-04

• Action: SELL

• Price: $101,497

---

Key Findings

1. The strategy significantly underperformed BTC buy-and-hold — +2.38% vs +31.50% over the same period
2. The crossover signal is **systematically contrarian** in BTC's market structure — **by the time MA200 confirms a move, the move is already exhausted**. Every crossover bought near local bottoms and sold near local tops
3. Max drawdown was -35.32% — less than BTC's -49.53%, but the strategy lost money regardless
4. Win rate is essentially 50/50 — the signal has no predictive edge in this asset's regime

---

Why This Matters

This is an honest backtest — not cherry-picked. The strategy fails, and that's the point. It demonstrates:

- Proper backtesting methodology (no look-ahead bias, clean data sourcing)
- Honest reporting of results — including negative outcomes
- Critical thinking about signal quality and market character

This is exactly the mindset needed for quant research roles.

---

Live Signal Monitor (May 2026)

MA20 is currently below MA200 (~$78,330 vs $82,880) — strategy is short.

If MA20 crosses back above MA200, the model generates a BUY signal. However, historical evidence suggests this may be another contrarian trap:

- Every past BUY signal occurred near local bottoms → sold near local tops
- Every SELL signal occurred near local bottoms → bought near local tops
- The crossover is slow (200-day average) — by the time it confirms, the move is exhausted

Pattern observed: The signal acts as a contrarian indicator in BTC's trending market — buying at what turns out to be near the bottom and selling at what turns out to be near the top.

Monitor live at: Binance BTCUSDT chart (https://www.binance.com/en/price/bitcoin)

---

How to Run

# Install dependencies
pip install pandas matplotlib requests

# Run the backtest
python run_backtest.py


Charts (btc_price_chart.png, equity_curve.png) and data (btc_price_data.csv) are generated automatically.

---

Files

- run_backtest.py — single-file Python backtest (data fetch + signals + charts)
- btc_price_data.csv — raw Binance daily OHLCV data
- btc_price_chart.png — BTC price with MA20/MA200 overlay
- equity_curve.png — strategy equity curve vs BTC, drawdown chart, trade markers

---

Disclaimer

This is a learning/research project. Not financial advice. Past performance does not predict future returns.
