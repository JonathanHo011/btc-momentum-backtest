# BTC MA20/MA200 Momentum Backtest — v3

**Live signal (May 22, 2026):** MA20 below MA200 → **FLAT**  
**BTC:** ~$77,457 | **Position:** Cash since Aug 25, 2025 trailing stop exit  
**Watch:** Monitoring for golden cross

---

## Performance Comparison

| Strategy | Total Return | Max Drawdown | Sharpe |
|---|---|---|---|
| **v3: MA + 10% Trail (FLAT)** 🔥 | **+58.09%** | **-12.73%** | **+1.012** |
| v2: MA xover (SHORT) | -41.81% | -58.56% | -0.271 |
| Buy & Hold | +75.32% | -49.53% | +0.689 |

**Key change from v2:** When MA20 < MA200, stays FLAT (cash) instead of going SHORT. Exiting to cash removes the whipsaw risk that destroyed v2's returns.

---

## v3 Trade Log

| Date | Action | Price | PnL | Exit Reason |
|------|--------|-------|-----|-------------|
| 2024-10-18 | BUY | $68,428 | — | Golden cross |
| 2024-12-22 | SELL | $95,186 | **+39.10%** | Trailing stop (10%) |
| 2025-05-02 | BUY | $96,887 | — | Golden cross |
| 2025-08-25 | SELL | $110,112 | **+13.65%** | Trailing stop (10%) |

Both exits were trailing stop breaches — the MA death cross never fired. The trailing stop exited 2-3 months earlier than the death cross would have.

---

## Why v2's Short Method Failed

```
Period                    Position   BTC moved           Effect
─────────────────────────────────────────────────────────────────────────
Mar 13 – Oct 18, 2024     SHORT      $73K → $68K (-7%)  GAIN (+7%)
Oct 18 – Mar 22, 2025     LONG       $68K → $84K (+23%) GAIN (+22.5%)
Mar 22 – May 2, 2025      SHORT      $84K → $97K (+15%) LOSS (-15%)  ← KILLER
May 2 – Nov 4, 2025       LONG       $97K → $101K (+5%) GAIN (+4.8%)
Nov 4 – May 22, 2026      SHORT      $101K → $77K (-24%) GAIN (+24%)
```

Being short during the March→May 2025 counter-trend rally (-15%) followed by daily compounding erosion through chop produced -42% total return. v3 fixes this by staying flat instead of shorting — the strategy only profits when the signal is clearly bullish.

---

## Strategy Logic (v3)

```
Entry:  MA20 crosses ABOVE MA200 → BUY (golden cross)
Exit:   Close drops 10% below highest close since entry → SELL (trailing stop)
         — OR —
        MA20 crosses BELOW MA200 → SELL (death cross, backup)

When MA20 < MA200: Stay FLAT (cash). Do NOT short.
The trailing stop ratchets UP only — never down.
```

---

## Related: CVD Backtest (Separate Repo)

CVD (Cumulative Volume Delta) was tested as entry and exit filter in a separate repo: [btc-cvd-backtest](https://github.com/JonathanHo011/btc-cvd-backtest). Both uses were **rejected** for daily spot BTC — documented with full postmortem.

---

## Setup

```bash
pip install pandas matplotlib requests
python run_backtest_v3.py
```

## Data Source

Binance public API — no key required. Forward fetch with deduplication.

---

## Version History

| Version | Date | Key Change | Return | MaxDD | Sharpe |
|---------|------|-----------|--------|-------|--------|
| **v3** | May 22, 2026 | 10% trailing stop + FLAT (no shorting) | **+58.09%** | **-12.73%** | **+1.012** |
| v2 | May 11, 2026 | Walk-forward + full metrics | +0.55% | -35.32% | -0.036 |
| v1 | May 9, 2026 | Initial MA crossover | +0.55% | -35.32% | -0.036 |
