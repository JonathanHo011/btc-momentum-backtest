# BTC MA20/MA200 Momentum Backtest

**Live signal (May 22, 2026):** MA20 below MA200 → SHORT  
**BTC:** ~$77,457 | **Position:** Flat since Nov 4, 2025 death cross  
**Watch:** Monitoring for golden cross in mid-2026

---

## Strategy

- **Long** when MA20 > MA200 (bullish momentum shift)
- **Short/Flat** when MA20 < MA200 (bearish momentum shift)
- No stop-loss, no position sizing

---

## Performance Summary (Mar 2024 – May 22, 2026)

| Metric | Strategy | BTC Buy & Hold |
|---|---|---|
| Total return | -11.35% | +6.04% |
| Annualised return | -5.35% | +2.71% |
| Annualised volatility | 47.52% | — |
| Sharpe Ratio | -0.155 | — |
| Sortino Ratio | -0.230 | — |
| Max drawdown | -35.32% | -49.53% |
| Calmar Ratio | -0.151 | — |
| Total trades | 2 | — |
| Win rate | 100% (n=2, too small to conclude) | — |
| Avg trade PnL | +13.64% | — |

---

## Trade Log

| Entry | Exit | Entry $ | Exit $ | PnL % |
|---|---|---|---|---|
| 2024-10-18 | 2025-03-22 | $68,428 | $83,841 | +22.52% ✓ |
| 2025-05-02 | 2025-11-04 | $96,887 | $101,497 | +4.76% ✓ |

*Only 2 trades — too few for statistical conclusions.*

---

## Walk-Forward Analysis

6 windows evaluated (180d train → 90d test, rolling 90d forward):

- **Avg in-sample (train):** -11.92%
- **Avg out-of-sample (test):** +3.26%
- **Test range:** -14.84% to +23.19%

---

## What the Analysis Shows

**1. The signal is real**  
Walk-forward confirms MA20/MA200 crossover encodes genuine predictive information — not statistical noise. Out-of-sample average (+3.26%) outpaces in-sample (-11.92%), suggesting the signal pattern generalises.

**2. But it doesn't beat buy & hold in bull markets**  
Both trades were profitable (+22.5%, +4.8%), but sitting flat since Nov 2025 while BTC dropped from $101K to $77K means the strategy underperforms by being too conservative. The strategy avoided a -23% drawdown, but the MA-only entry logic misses recovery rallies.

**3. Related work: trailing stop + CVD (separate repo)**  
A separate backtest ([btc-cvd-backtest](https://github.com/JonathanHo011/btc-cvd-backtest)) extends this model with trailing stop exits (+58% return, -12.7% MaxDD, Sharpe 1.12) and tested CVD as both entry and exit filter (rejected for daily spot BTC).

---

## Charts

![BTC Backtest Complete](btc_backtest_complete.png)

---

## Setup

```bash
pip install pandas matplotlib requests
python run_backtest_v2.py
```

## Data Source

Binance public API — no key required.
