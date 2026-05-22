# BTC MA20/MA200 Momentum Backtest — v3

**Live signal (May 22, 2026):** MA20 below MA200 → **FLAT**  
**BTC:** ~$77,452 | **Position:** Cash since Aug 25, 2025 trailing stop exit  
**Watch:** Monitoring for golden cross

---

## Core Finding: Shorting Destroys Returns

Two methods, same MA crossover entries, same data — only the exit logic differs. The gap is decisive:

### Performance Comparison (Mar 13, 2024 → May 22, 2026)

| Strategy | Total Return | Max Drawdown | Sharpe |
|---|---|---|---|
| **v3: MA + 10% Trail (FLAT)** 🔥 | **+58.09%** | **-12.73%** | **+1.062** |
| v2: MA xover (SHORT) | -11.31% | -35.32% | +0.148 |
| Buy & Hold | +5.99% | -49.53% | +0.318 |

---

## Why Shorting Fails (v2 Breakdown)

| Period | Position | BTC Move | Strategy Effect |
|---|---|---|---|
| Mar 13 – Oct 17, 2024 | Mostly LONG | $73K → $67K (-7.7%) | **-27.93%** — volatility drag in choppy drift-down |
| Oct 18 – Mar 22, 2025 | LONG (Trade 1) | $68K → $84K (+22.5%) | **+20.70%** ✅ |
| Mar 23 – May 1, 2025 | SHORT | $86K → $96K (+12.1%) | **-15.49%** — forced short during counter-trend rally |
| May 2 – Nov 4, 2025 | LONG (Trade 2) | $97K → $101K (+4.8%) | **+4.33%** ✅ |
| Nov 5 – May 22, 2026 | SHORT | $104K → $77K (-25.4%) | **+15.65%** ✅ |

Both long trades were profitable (+20.7%, +4.3%), and the post-Nov 2025 short was profitable (+15.7%). But the two loss periods were catastrophic enough to produce an overall **-11.31%** loss vs **+5.99%** buy & hold.

The worst offender was Mar–Oct 2024: BTC only drifted down -7.7%, but being long through 7 months of choppy sideways action produced -27.9% strategy loss through daily compounding and volatility drag.

---

## v3 Fix: Trailing Stop + Cash

v3 eliminates both problems:
- **No shorting** — stays flat when MA20 < MA200 rather than going short
- **10% trailing stop** — exits early rather than riding drawdowns

### v3 Trade Log

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
| v2 | May 11, 2026 | Walk-forward + full metrics (SHORT) | -11.31% | -35.32% | +0.148 | ❌ Shorting fails |
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
