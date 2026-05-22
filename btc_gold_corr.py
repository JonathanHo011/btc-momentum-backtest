"""
BTC vs Gold (PAXG) Correlation Study — May 22, 2026 Update
===========================================================
Regime analysis: how BTC and gold move together under different
market conditions. Uses Binance BTC + PAXG daily data.

Run: python btc_gold_corr.py
"""

import requests
import pandas as pd
import numpy as np

# ============================================================
# 1. FETCH BTC & PAXG daily klines from Binance
# ============================================================
print("Fetching BTC + PAXG daily data from Binance...")

def fetch_binance(symbol, limit=1000):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": "1d", "limit": limit}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    df = pd.DataFrame(r.json(), columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "count",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["date"] = pd.to_datetime(df["open_time"], unit="ms").dt.date
    df["close"] = df["close"].astype(float)
    return df.set_index("date")[["close"]]

btc = fetch_binance("BTCUSDT")
paxg = fetch_binance("PAXGUSDT")

# Merge on date
merged = btc.join(paxg, lsuffix="_btc", rsuffix="_paxg").dropna()
merged.columns = ["btc", "paxg"]
merged["btc_return"] = merged["btc"].pct_change()
merged["paxg_return"] = merged["paxg"].pct_change()

print(f"  BTC:  {btc.index[0]} → {btc.index[-1]}  ({len(btc)} days)")
print(f"  PAXG: {paxg.index[0]} → {paxg.index[-1]}  ({len(paxg)} days)")
print(f"  Merged range: {merged.index[0]} → {merged.index[-1]}  ({len(merged)} days)")

# ============================================================
# 2. DEFINE REGIMES (based on BTC price action)
# ============================================================
# Use ATH date as known: Oct 6, 2025 ($124,659 close)
ATH_DATE = pd.to_datetime("2025-10-06").date()
CEASEFIRE_DATE = pd.to_datetime("2026-04-10").date()  # approx Iran ceasefire

regimes = {
    "1: Pre-ATH Rally\n   (Start → Oct 6 2025)":
        merged.index <= ATH_DATE,
    "2: Post-ATH Drawdown\n   (Oct 7 2025 → Apr 9 2026)":
        (merged.index > ATH_DATE) & (merged.index <= CEASEFIRE_DATE),
    "3: Post-Ceasefire Recovery\n   (Apr 10 2026 → today)":
        merged.index > CEASEFIRE_DATE,
}

# ============================================================
# 3. CORRELATION ANALYSIS
# ============================================================
print(f"\n{'='*70}")
print(f"BTC vs PAXG (Gold) — Correlation by Regime")
print(f"{'='*70}")

results = []

for label, mask in regimes.items():
    data = merged[mask]
    if len(data) < 10:
        print(f"\n{label}")
        print(f"  Not enough data ({len(data)} days)")
        continue

    corr_price = data["btc"].corr(data["paxg"])
    corr_ret = data["btc_return"].corr(data["paxg_return"])
    btc_change = (data["btc"].iloc[-1] / data["btc"].iloc[0] - 1) * 100
    paxg_change = (data["paxg"].iloc[-1] / data["paxg"].iloc[0] - 1) * 100

    btc_start = data["btc"].iloc[0]
    btc_end = data["btc"].iloc[-1]
    paxg_start = data["paxg"].iloc[0]
    paxg_end = data["paxg"].iloc[-1]

    print(f"\n{label}")
    print(f"  {len(data):,d} days")
    print(f"  BTC:  ${btc_start:,.0f} → ${btc_end:,.0f}  ({btc_change:+.2f}%)")
    print(f"  PAXG: ${paxg_start:,.0f} → ${paxg_end:,.0f}  ({paxg_change:+.2f}%)")
    print(f"  Price correlation:  {corr_price:+.3f}")
    print(f"  Return correlation: {corr_ret:+.3f}")

    results.append({
        "regime": label.split("\n")[0],
        "days": len(data),
        "btc_change": btc_change,
        "paxg_change": paxg_change,
        "corr_price": corr_price,
        "corr_ret": corr_ret,
    })

# Full period
full_corr_price = merged["btc"].corr(merged["paxg"])
full_corr_ret = merged["btc_return"].corr(merged["paxg_return"])
btc_full = (merged["btc"].iloc[-1] / merged["btc"].iloc[0] - 1) * 100
paxg_full = (merged["paxg"].iloc[-1] / merged["paxg"].iloc[0] - 1) * 100

print(f"\n{'─'*70}")
print(f"FULL PERIOD ({merged.index[0]} → {merged.index[-1]})")
print(f"  BTC:  {btc_full:+.2f}%")
print(f"  PAXG: {paxg_full:+.2f}%")
print(f"  Price correlation:  {full_corr_price:+.3f}")
print(f"  Return correlation: {full_corr_ret:+.3f}")

# ============================================================
# 4. KEY INSIGHTS
# ============================================================
print(f"\n{'='*70}")
print(f"KEY INSIGHTS")
print(f"{'='*70}")

# Check if any regime has correlation > 0.5 (meaningful)
high_corr = [r for r in results if abs(r["corr_price"]) > 0.5]
if high_corr:
    for r in high_corr:
        direction = "together" if r["corr_price"] > 0 else "opposite"
        print(f"  {r['regime']}: BTC & PAXG moved {direction} (corr={r['corr_price']:+.3f})")
else:
    print(f"  No regime showed meaningful price correlation (> |0.5|)")

# Inflation hedge test: check recent data
if len(regimes) >= 3:
    r3 = results[2] if len(results) > 2 else None
    if r3:
        print(f"\n  Post-ceasefire: BTC {r3['btc_change']:+.2f}% | PAXG {r3['paxg_change']:+.2f}% | corr={r3['corr_price']:+.3f}")
        if r3["btc_change"] > 0 and r3["paxg_change"] < 0:
            print("  → BTC rising while gold falling = risk-on recovery, NOT inflation hedge")
        elif r3["btc_change"] > 0 and r3["paxg_change"] > 0:
            print("  → Both rising — could indicate shared macro driver (inflation, liquidity)")
        elif r3["btc_change"] < 0 and r3["paxg_change"] > 0:
            print("  → Gold rising while BTC falling = classic risk-off / safe haven rotation")

print("\nDone.")
