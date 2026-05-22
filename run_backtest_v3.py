"""
BTC MA20/MA200 Momentum Backtest — v3 (Trailing Stop + No Shorting)
====================================================================
Key changes from v2:
  - When MA20 < MA200, stays FLAT (cash) instead of going SHORT
  - Exit uses 10% trailing stop from highest close since entry
  - MA death cross is a backup exit only
  - Direct comparison: old method (SHORT) vs new method (FLAT + trailing stop)

Run: python run_backtest_v3.py
Output: btc_backtest_v3.png
"""

import requests, math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ============================================================
# 1. FETCH DATA (forward fetch, deduped — same as v6)
# ============================================================
print("Fetching BTCUSDT daily klines from Binance...")
FETCH_START_MS = 1692662400000  # Aug 1, 2023

all_klines = []
batch = 500
start_time = FETCH_START_MS

while len(all_klines) < 2000:
    params = {"symbol": "BTCUSDT", "interval": "1d", "limit": batch, "startTime": start_time}
    r = requests.get("https://api.binance.com/api/v3/klines", params=params)
    r.raise_for_status()
    batch_data = r.json()
    if not batch_data:
        break
    all_klines.extend(batch_data)
    last_ts = int(batch_data[-1][0])
    start_time = last_ts + 86400000
    if start_time > 1767225600000:
        break

# Deduplicate
seen = set()
deduped = []
for k in all_klines:
    if k[0] not in seen:
        seen.add(k[0])
        deduped.append(k)

print(f"  {len(all_klines)} fetched, {len(deduped)} unique")

df = pd.DataFrame(deduped, columns=[
    "open_time", "open", "high", "low", "close", "volume",
    "close_time", "quote_volume", "count",
    "taker_buy_base", "taker_buy_quote", "ignore"
])
df["dt"] = pd.to_datetime(df["open_time"], unit="ms")
for col in ["close", "open", "high", "low", "volume"]:
    df[col] = df[col].astype(float)
df = df.sort_values("dt").reset_index(drop=True)

# ============================================================
# 2. INDICATORS
# ============================================================
df["ma20"] = df["close"].rolling(20).mean()
df["ma200"] = df["close"].rolling(200).mean()

# MA crossover signals
df["ma_cross"] = 0
for i in range(200, len(df) - 1):
    if pd.notna(df["ma20"].iloc[i]) and pd.notna(df["ma200"].iloc[i]) and pd.notna(df["ma20"].iloc[i-1]):
        if df["ma20"].iloc[i-1] < df["ma200"].iloc[i-1] and df["ma20"].iloc[i] >= df["ma200"].iloc[i]:
            df.loc[df.index[i], "ma_cross"] = 1   # golden cross
        elif df["ma20"].iloc[i-1] > df["ma200"].iloc[i-1] and df["ma20"].iloc[i] <= df["ma200"].iloc[i]:
            df.loc[df.index[i], "ma_cross"] = -1  # death cross

first_valid = df[df["ma200"].notna()]["dt"].iloc[0]
print(f"  MA200 first valid: {first_valid.strftime('%Y-%m-%d')}")

# ============================================================
# 3. BACKTEST — OLD METHOD (v2: long + SHORT when MA20<MA200)
# ============================================================
BACKTEST_START = "2024-01-01"
start_idx = df[df["dt"] >= pd.to_datetime(BACKTEST_START)].index[0]

btc_only = df.iloc[start_idx:].copy().reset_index(drop=True)

# Filter to where MA200 is valid — same as original v2 logic
btc_only = btc_only[btc_only["ma200"].notna()].copy().reset_index(drop=True)
btc_only["signal"] = (btc_only["ma20"] > btc_only["ma200"]).astype(int)
btc_only["position"] = btc_only["signal"].replace(0, -1)  # 1=long, -1=short
btc_only["daily_return"] = btc_only["close"].pct_change().fillna(0)
btc_only["strategy_return"] = btc_only["daily_return"] * btc_only["position"].shift(1).fillna(0)
btc_only["equity"] = (1 + btc_only["strategy_return"]).cumprod()
btc_only["btc_equity"] = (1 + btc_only["daily_return"]).cumprod()

# ============================================================
# 4. BACKTEST — NEW METHOD (v3: long + FLAT, trailing stop exit)
# ============================================================
TRAIL_PCT = 0.10

in_position = False
entry_price = 0.0
shares_held = 0.0
trail_high = 0.0
stop_level = 0.0
equity_v3 = 10000.0
equity_curve_v3 = []
trades_v3 = []

for i in range(len(btc_only)):
    row = btc_only.iloc[i]
    prev = btc_only.iloc[i - 1] if i > 0 else None

    if pd.isna(row["ma20"]) or pd.isna(row["ma200"]):
        equity_curve_v3.append(equity_v3)
        continue

    # ENTRY: golden cross
    if prev is not None and not in_position:
        ma_crossing_up = (prev["ma_cross"] == 0 and row["ma_cross"] == 1)
        if ma_crossing_up:
            in_position = True
            entry_price = row["close"]
            shares_held = equity_v3 / entry_price
            trail_high = entry_price
            stop_level = trail_high * (1 - TRAIL_PCT)
            trades_v3.append({"type": "BUY", "date": row["dt"], "price": entry_price})

    # EXIT: trailing stop OR death cross
    elif prev is not None and in_position:
        ma_crossing_down = (prev["ma_cross"] == 0 and row["ma_cross"] == -1)
        trail_high = max(trail_high, row["close"])
        stop_level = trail_high * (1 - TRAIL_PCT)
        stop_breached = (row["close"] <= stop_level)

        if ma_crossing_down or stop_breached:
            exit_price = row["close"]
            equity_v3 = shares_held * exit_price
            pnl_pct = (exit_price - entry_price) / entry_price * 100
            reason = "DEATH CROSS" if ma_crossing_down else f"TRAILING STOP ({TRAIL_PCT*100:.0f}%)"
            trades_v3.append({"type": "SELL", "date": row["dt"], "price": exit_price,
                              "pnl_pct": pnl_pct, "reason": reason})
            in_position = False
            shares_held = 0.0

    # Mark-to-market
    if in_position:
        equity_curve_v3.append(shares_held * row["close"])
    else:
        equity_curve_v3.append(equity_v3)

# Close open position if any
if in_position:
    last_close = btc_only.iloc[-1]["close"]
    equity_v3 = shares_held * last_close
    pnl = (last_close - entry_price) / entry_price * 100
    equity_curve_v3[-1] = equity_v3
    trades_v3.append({"type": "CLOSE", "date": btc_only.iloc[-1]["dt"],
                      "price": last_close, "pnl_pct": pnl, "reason": "END OF DATA"})

equity_v3_series = np.array(equity_curve_v3) / equity_curve_v3[0]  # normalize to 1

# ============================================================
# 5. PERFORMANCE METRICS — both methods
# ============================================================
def max_dd(series):
    peak = np.maximum.accumulate(series)
    dd = (series - peak) / peak
    return dd.min()

def calc_sharpe(eq, rf=0.02):
    rets = np.diff(eq) / eq[:-1]
    if len(rets) == 0 or rets.std() == 0:
        return 0.0
    ann_ret = rets.mean() * 365
    ann_vol = rets.std() * np.sqrt(365)
    return (ann_ret - rf) / ann_vol

def calc_metrics(label, eq_series):
    total_days = len(eq_series)
    total_ret = eq_series[-1] / eq_series[0] - 1
    ann_ret = (1 + total_ret) ** (365 / total_days) - 1
    dd = max_dd(eq_series)
    sharpe = calc_sharpe(eq_series)
    return {
        "label": label,
        "total_ret": total_ret,
        "ann_ret": ann_ret,
        "max_dd": dd,
        "sharpe": sharpe,
    }

# Metrics
v2_eq = btc_only["equity"].values
v3_eq = equity_v3_series
bh_eq = btc_only["btc_equity"].values

metrics = [
    calc_metrics("v2 (MA xover, SHORT)", v2_eq),
    calc_metrics("v3 (MA + 10% Trail, FLAT)", v3_eq),
    calc_metrics("Buy & Hold", bh_eq),
]

print(f"\n{'='*70}")
print(f"PERFORMANCE COMPARISON  ({BACKTEST_START} → {btc_only['dt'].iloc[-1].strftime('%Y-%m-%d')})")
print(f"{'='*70}")
print(f"  {'Strategy':<30s} {'Total Ret':>9s}  {'Max DD':>8s}  {'Sharpe':>7s}")
print(f"  {'-'*56}")
for m in metrics:
    print(f"  {m['label']:<30s} {m['total_ret']:+8.2%}  {m['max_dd']:+8.2%}  {m['sharpe']:+8.3f}")
print(f"{'='*70}")

# ============================================================
# 6. TRADE LOG
# ============================================================
print(f"\nTrade Log (v3 — trailing stop):")
print(f"  {'Date':<12} {'Action':<6} {'Price':>10} {'PnL':>9}  {'Reason'}")
print(f"  {'-'*55}")
for t in trades_v3:
    pnl_str = f"{t.get('pnl_pct', 0):+.2f}%" if t["type"] in ("SELL", "CLOSE") else ""
    reason = t.get("reason", "")
    print(f"  {t['date'].strftime('%Y-%m-%d'):<12} {t['type']:<6} ${t['price']:>9,.0f} {pnl_str:>9}  {reason}")

# ============================================================
# 7. PLOT — 3 panels, dark theme
# ============================================================
plt.close("all")
fig, axes = plt.subplots(3, 1, figsize=(16, 14), facecolor="#0d1117")
C = {
    "bg": "#0d1117", "fg": "#e6edf3",
    "ma20": "#f0b429", "ma200": "#58a6ff",
    "v2": "#f85149", "v3": "#3fb950", "btc": "#8b949e",
    "up": "#3fb950", "dn": "#f85149",
    "trail": "#d2991d",  # orange for trailing stop exits
}

for ax in axes:
    ax.set_facecolor(C["bg"])
    ax.tick_params(colors=C["fg"])
    ax.spines["bottom"].set_color(C["fg"])
    ax.spines["left"].set_color(C["fg"])
    ax.title.set_color(C["fg"])

# --- Panel 1: Price + MAs ---
ax1 = axes[0]
ax1.plot(btc_only["dt"], btc_only["close"],  color=C["fg"],    lw=1,   alpha=0.5, label="BTC")
ax1.plot(btc_only["dt"], btc_only["ma20"],   color=C["ma20"],  lw=1.2, label="MA20")
ax1.plot(btc_only["dt"], btc_only["ma200"],  color=C["ma200"], lw=1.2, label="MA200")

# Trade markers (v3)
for t in trades_v3:
    if t["type"] == "BUY":
        ax1.scatter(t["date"], t["price"], marker="^", color=C["up"], s=100, zorder=5)
    elif t["type"] in ("SELL", "CLOSE"):
        is_trail = "TRAILING" in t.get("reason", "")
        color = C["trail"] if is_trail else C["dn"]
        marker = "s" if is_trail else "v"
        ax1.scatter(t["date"], t["price"], marker=marker, color=color, s=100, zorder=5)

ax1.set_title("BTCUSDT — MA20/MA200 + 10% Trailing Stop (v3)", fontsize=13, pad=10)
ax1.legend(loc="upper left", framealpha=0.2)
ax1.set_ylabel("Price (USD)")
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

# Live signal
ma20_v = btc_only["ma20"].iloc[-1]
ma200_v = btc_only["ma200"].iloc[-1]
signal_str = f"MA20 (${ma20_v:,.0f}) {'>' if ma20_v > ma200_v else '<'} MA200 (${ma200_v:,.0f})  |  {'LONG' if ma20_v > ma200_v else 'FLAT'}"
ax1.annotate(signal_str,
             xy=(btc_only["dt"].iloc[-1], btc_only["close"].iloc[-1]),
             xytext=(10, -30), textcoords="offset points",
             color=C["fg"], fontsize=9,
             arrowprops=dict(arrowstyle="->", color=C["fg"], lw=0.8))

# --- Panel 2: Equity curves ---
ax2 = axes[1]
ax2.plot(btc_only["dt"], v3_eq,  color=C["v3"],  lw=2.0, label="v3: MA + 10% Trail (FLAT)")
ax2.plot(btc_only["dt"], v2_eq,  color=C["v2"],  lw=1.5, label="v2: MA xover (SHORT)", alpha=0.7)
ax2.plot(btc_only["dt"], bh_eq,  color=C["btc"], lw=1.2, label="Buy & Hold", alpha=0.6, linestyle="--")

ax2.set_title("Equity Curve Comparison", fontsize=13, pad=10)
ax2.legend(loc="upper left", framealpha=0.2)
ax2.set_ylabel("Cumulative Return (×)")
ax2.axhline(1.0, color=C["fg"], lw=0.6, alpha=0.3, linestyle="--")
ax2.set_ylim(0.4, 1.8)
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

# --- Panel 3: Drawdown comparison ---
ax3 = axes[2]

def dd_series(eq):
    peak = np.maximum.accumulate(eq)
    return (eq - peak) / peak * 100

ax3.fill_between(btc_only["dt"], dd_series(v2_eq), 0, color=C["v2"], alpha=0.2, label="v2 Drawdown")
ax3.plot(btc_only["dt"], dd_series(v2_eq), color=C["v2"], linewidth=0.8)
ax3.fill_between(btc_only["dt"], dd_series(v3_eq), 0, color=C["v3"], alpha=0.3, label="v3 Drawdown")
ax3.plot(btc_only["dt"], dd_series(v3_eq), color=C["v3"], linewidth=1.0)
ax3.set_title("Drawdown Comparison", fontsize=13, pad=10)
ax3.legend(loc="lower left", framealpha=0.2)
ax3.set_ylabel("Drawdown (%)")
ax3.set_ylim(-60, 5)
ax3.axhline(0, color=C["fg"], lw=0.6, alpha=0.3, linestyle="--")
ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)

plt.tight_layout(pad=2.0)
plt.savefig("btc_backtest_v3.png", dpi=150, bbox_inches="tight", facecolor=C["bg"])
print(f"\n  → Chart saved: btc_backtest_v3.png")

# Save CSV with indicators
df.to_csv("btc_price_data.csv", index=False)
print(f"  → Data saved: btc_price_data.csv")
print("Done.")
