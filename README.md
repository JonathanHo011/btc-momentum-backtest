# BTC MA20/MA200 Momentum Backtest — v3

**Live signal (May 22, 2026):** MA20 below MA200 → **FLAT**  
**BTC:** ~$77,457 | **Position:** Cash since Aug 25, 2025 trailing stop exit  
**Watch:** Monitoring for golden cross

---

## Core Finding: Shorting Destroys Returns

Two methods, same MA crossover entries, same data — only the exit logic differs. The gap is decisive:

### Performance Comparison (Mar 8, 2024 → May 22, 2026)

| Strategy | Total Return | Max Drawdown | Sharpe |
|---|---|---|---|
| **v3: MA + 10% Trail (FLAT)** 🔥 | **+58.09%** | **-12.73%** | **+1.062** |
| v2: MA xover (SHORT) | -4.87% | -35.32% | +0.148 |
| Buy & Hold | +13.70% | -49.53% | +0.318 |

**The short method loses money.** Despite two profitable long trades (+22.5% and +4.8% each), being forced short between them gave back the gains:

```
Mar 22 – May 2, 2025    SHORT during +15% BTC rally    → -15% loss
Nov 4 – May 22, 2026    SHORT during choppy downtrend   → volatility drag erosion
```

Going to cash eliminates this. v3 stays flat between trades and uses a 10% trailing stop to exit — Sharpe above 1.0 for the first time.

---

## v3 Trade Log

| Date | Action | Price | PnL | Exit Reason |
|------|--------|-------|-----|-------------|
| 2024-10-18 | BUY | $68,428 | — | Golden cross |
| 2024-12-22 | SELL | $95,186 | **+39.10%** | Trailing stop (10%) |
| 2025-05-02 | BUY | $96,887 | — | Golden cross |
| 2025-08-25 | SELL | $110,112 | **+13.65%** | Trailing stop (10%) |

Both exits triggered by the trailing stop — the MA death cross never fired.

---

## Strategy Logic (v3 — Current)

```
Entry:  MA20 crosses ABOVE MA200 → BUY (golden cross)
Exit:   Close drops 10% below highest close since entry → SELL (trailing stop)
         — OR —
        MA20 crosses BELOW MA200 → SELL (death cross, backup)

When MA20 < MA200: Stay FLAT (cash). Do NOT short.
The trailing stop ratchets UP only — never down.
```

---

## Charts

![BTC Backtest v3](btc_backtest_v3.png)

---

## Version History

| Version | Date | Key Change | Return | MaxDD | Sharpe | Verdict |
|---------|------|-----------|--------|-------|--------|---------|
| **v3** | May 22, 2026 | 10% trailing stop + FLAT (no shorting) | **+58.09%** | **-12.73%** | **+1.062** | ✅ Best |
| v2 | May 11, 2026 | Walk-forward + full metrics (SHORT) | -4.87% | -35.32% | +0.148 | ❌ Shorting fails |
| v1 | May 9, 2026 | Initial MA crossover (SHORT) | +0.55% | -35.32% | -0.036 | 🏁 Baseline |

---

## Related: CVD Backtest (Separate Repo)

CVD was tested as both entry and exit filter across 3 versions — [btc-cvd-backtest](https://github.com/JonathanHo011/btc-cvd-backtest). Rejected for daily spot BTC.

---

## Setup

```bash
pip install pandas matplotlib requests
python run_backtest_v3.py
```

## Data Source

Binance public API — no key required.
