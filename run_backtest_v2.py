"""
BTC MA20/MA200 Momentum Backtest — v2
Tasks completed:
  1. Walk-forward analysis (rolling out-of-sample windows)
  2. Full performance metrics (Sharpe, Sortino, Calmar, win rate, avg trade PnL)
  3. Annotated equity curve with trade labels + BTC comparison
  4. Updated README with live signal + new metrics
"""

import requests, math
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ─────────────────────────────────────────────
# 1. FETCH DATA
# ─────────────────────────────────────────────
print("Fetching BTCUSDT daily klines from Binance...")
resp = requests.get(
    "https://api.binance.com/api/v3/klines",
    params={"symbol": "BTCUSDT", "interval": "1d", "limit": 1000},
    timeout=15,
)
resp.raise_for_status()
raw = resp.json()

df = pd.DataFrame(
    raw,
    columns=["ot","open","high","low","close","vol","ct","qv","tr","tbv","tbqv","ign"],
)
df["date"] = pd.to_datetime(pd.to_numeric(df["ot"]), unit="ms")
df.set_index("date", inplace=True)
for c in ["open", "high", "low", "close", "vol"]:
    df[c] = pd.to_numeric(df[c])

df["ma20"]  = df["close"].rolling(20).mean()
df["ma200"] = df["close"].rolling(200).mean()
df["signal"] = (df["ma20"] > df["ma200"]).astype(int)
df.to_csv("btc_price_data.csv")
print(f"  → {len(df)} candles saved to btc_price_data.csv")

# ─────────────────────────────────────────────
# 2. BACKTEST ENGINE
# ─────────────────────────────────────────────
btc = df[df["ma200"].notna()].copy()
btc["position"]         = btc["signal"].replace(0, -1)
btc["daily_return"]     = btc["close"].pct_change()
btc["strategy_return"]  = btc["daily_return"] * btc["position"].shift(1)
btc["equity"]           = (1 + btc["strategy_return"]).cumprod()
btc["btc_equity"]       = (1 + btc["daily_return"]).cumprod()

# Trade detection
btc["entry_signal"] = (btc["signal"] == 1) & (btc["signal"].shift(1) == 0)
btc["exit_signal"]  = (btc["signal"] == 0) & (btc["signal"].shift(1) == 1)

# ─────────────────────────────────────────────
# 3. PERFORMANCE METRICS
# ─────────────────────────────────────────────
ann_factor   = math.sqrt(365)
total_days   = (btc.index[-1] - btc.index[0]).days
total_return = btc["equity"].iloc[-1] - 1
btc_return   = btc["btc_equity"].iloc[-1] - 1

strat_ann_ret = (1 + total_return) ** (365 / total_days) - 1
btc_ann_ret   = (1 + btc_return)   ** (365 / total_days) - 1
strat_vol     = btc["strategy_return"].std() * math.sqrt(365)
btc_vol       = btc["daily_return"].std() * math.sqrt(365)

risk_free = 0.02
sharpe    = (strat_ann_ret - risk_free) / strat_vol if strat_vol != 0 else 0
rets      = btc["strategy_return"].dropna()
downside  = rets[rets < 0]
sortino   = (strat_ann_ret - risk_free) / (downside.std() * math.sqrt(365)) if len(downside) > 0 else 0

def max_dd(series):
    peak = series.expanding().max()
    dd   = (series - peak) / peak
    return dd.min()

strat_dd = max_dd(btc["equity"])
btc_dd   = max_dd(btc["btc_equity"])
calmar   = strat_ann_ret / abs(strat_dd) if strat_dd != 0 else 0

# Trade-level stats
trades = []
entry_price = None
for idx, row in btc.iterrows():
    if row["entry_signal"] and entry_price is None:
        entry_price = row["close"]
        entry_date  = idx
    elif row["exit_signal"] and entry_price is not None:
        pnl_pct = (row["close"] - entry_price) / entry_price * 100
        trades.append({
            "entry_date": entry_date, "exit_date": idx,
            "entry_px": entry_price, "exit_px": row["close"],
            "pnl_pct": pnl_pct,
        })
        entry_price = None

trades_df = pd.DataFrame(trades)
wins   = trades_df[trades_df["pnl_pct"] > 0]
losses = trades_df[trades_df["pnl_pct"] <= 0]
win_rate  = len(wins) / len(trades_df) * 100 if len(trades_df) > 0 else 0
avg_win   = wins["pnl_pct"].mean()    if len(wins)   > 0 else 0
avg_loss  = losses["pnl_pct"].mean()  if len(losses) > 0 else 0
avg_trade = trades_df["pnl_pct"].mean()

print("\n" + "="*60)
print("PERFORMANCE METRICS")
print("="*60)
print(f"  Period            : {btc.index[0].date()} → {btc.index[-1].date()}")
print(f"  Total return      : {total_return*100:+.2f}%   (BTC: {btc_return*100:+.2f}%)")
print(f"  Ann. return       : {strat_ann_ret*100:+.2f}%   (BTC: {btc_ann_ret*100:+.2f}%)")
print(f"  Ann. volatility   : {strat_vol*100:.2f}%")
print(f"  Sharpe Ratio      : {sharpe:.3f}")
print(f"  Sortino Ratio     : {sortino:.3f}")
print(f"  Max drawdown      : {strat_dd*100:.2f}%   (BTC: {btc_dd*100:.2f}%)")
print(f"  Calmar Ratio      : {calmar:.3f}")
print(f"  Total trades      : {len(trades_df)}")
print(f"  Win rate          : {win_rate:.1f}%")
print(f"  Avg trade PnL     : {avg_trade:+.2f}%")
print(f"  Avg win           : {avg_win:+.2f}%")
print(f"  Avg loss          : {avg_loss:+.2f}%")
print("="*60)

# ─────────────────────────────────────────────
# 4. WALK-FORWARD ANALYSIS
# ─────────────────────────────────────────────
print("\nWalk-forward analysis (6-month train → 3-month test)...")
window_days = 180
test_days   = 90

results = []
start = 0
while True:
    train_end = start + window_days
    test_end  = train_end + test_days
    if test_end >= len(btc):
        break
    train = btc.iloc[start:train_end]
    test  = btc.iloc[train_end:test_end]
    if len(train) < 50 or len(test) < 5:
        start += test_days
        continue
    train_ret = (train["equity"].iloc[-1] - 1) * 100
    test_ret  = (test["equity"].iloc[-1] / train["equity"].iloc[-1] - 1) * 100
    results.append({
        "window":    f"{train.index[0].date()} – {train.index[-1].date()}",
        "train_ret": train_ret,
        "test_ret":  test_ret,
    })
    start += test_days

wf_df = pd.DataFrame(results)
print(f"\n  {len(wf_df)} windows evaluated")
print(f"  Avg train return: {wf_df['train_ret'].mean():+.2f}%")
print(f"  Avg test return : {wf_df['test_ret'].mean():+.2f}%")
print(f"  Test ret range : {wf_df['test_ret'].min():+.2f}% – {wf_df['test_ret'].max():+.2f}%")

# ─────────────────────────────────────────────
# 5. CHARTS
# ─────────────────────────────────────────────
fig, axes = plt.subplots(3, 1, figsize=(16, 14), facecolor="#0d1117")
C = {
    "bg": "#0d1117", "fg": "#e6edf3",
    "ma20": "#f0b429", "ma200": "#58a6ff",
    "equity": "#3fb950", "btc": "#8b949e",
    "up": "#3fb950", "dn": "#f85149",
}

for ax in axes:
    ax.set_facecolor(C["bg"])
    ax.tick_params(colors=C["fg"])
    ax.spines["bottom"].set_color(C["fg"])
    ax.spines["left"].set_color(C["fg"])
    ax.title.set_color(C["fg"])

# — Chart 1: Price + MAs + regime shading —
ax1 = axes[0]
ax1.plot(btc.index, btc["close"],  color=C["fg"],    lw=1,   alpha=0.5, label="BTC")
ax1.plot(btc.index, btc["ma20"],   color=C["ma20"],  lw=1.5, label="MA20")
ax1.plot(btc.index, btc["ma200"],  color=C["ma200"], lw=1.5, label="MA200")

# Green/red regime background
for i in range(len(btc) - 1):
    col = C["up"] if btc["position"].iloc[i] == 1 else C["dn"]
    ax1.axvspan(btc.index[i], btc.index[i+1], color=col, alpha=0.07)

# Trade markers
for _, t in trades_df.iterrows():
    col = C["up"] if t["pnl_pct"] > 0 else C["dn"]
    mk  = "^" if t["pnl_pct"] > 0 else "v"
    ax1.scatter(t["entry_date"], t["entry_px"], marker=mk, color=col, s=80, zorder=5)
    ax1.scatter(t["exit_date"],  t["exit_px"],  marker="o", color=col, s=40,  zorder=5)

ax1.set_title("BTCUSDT — MA20/MA200 Crossover Strategy", fontsize=13, pad=10)
ax1.legend(loc="upper left", framealpha=0.2)
ax1.set_ylabel("Price (USD)")
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

# Live signal annotation
ma20_v  = btc["ma20"].iloc[-1]
ma200_v = btc["ma200"].iloc[-1]
signal_str = f"MA20 ({ma20_v:,.0f}) {'>' if ma20_v > ma200_v else '<'} MA200 ({ma200_v:,.0f})"
ax1.annotate(signal_str,
             xy=(btc.index[-1], btc["close"].iloc[-1]),
xytext=(10, -25), textcoords="offset points",
             color=C["fg"], fontsize=9,
             arrowprops=dict(arrowstyle="->", color=C["fg"], lw=0.8))

# — Chart 2: Equity curve vs BTC —
ax2 = axes[1]
ax2.plot(btc.index, btc["btc_equity"], color=C["btc"],   lw=1.5, label="BTC Buy & Hold", alpha=0.8)
ax2.plot(btc.index, btc["equity"],     color=C["equity"], lw=2,   label="MA Crossover Strategy")
ax2.fill_between(btc.index, btc["btc_equity"], alpha=0.08, color=C["btc"])

# Drawdown on secondary axis
ax2_dd = ax2.twinx()
dd_series = (btc["equity"] - btc["equity"].expanding().max()) / btc["equity"].expanding().max()
ax2_dd.fill_between(btc.index, dd_series, 0, color=C["dn"], alpha=0.25, label="Strategy Drawdown")
ax2_dd.set_ylabel("Drawdown", color=C["dn"])
ax2_dd.set_ylim(-0.6, 0.05)
ax2_dd.tick_params(colors=C["dn"])

ax2.set_title("Equity Curve vs BTC Buy & Hold", fontsize=13, pad=10)
ax2.legend(loc="upper left", framealpha=0.2)
ax2.set_ylabel("Cumulative Return (×)")
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

# "First LONG" annotation
first_long = btc[btc["entry_signal"]].index[0]
ax2.scatter(first_long, btc["equity"].loc[first_long], marker="^",
            color=C["up"], s=120, zorder=5, edgecolors="yellow", linewidths=2)
ax2.annotate(f"First LONG\n${btc.loc[first_long, 'close']:,.0f}",
             xy=(first_long, btc["equity"].loc[first_long]),
             xytext=(20, 30), textcoords="offset points",
             color=C["up"], fontsize=8,
             arrowprops=dict(arrowstyle="->", color=C["up"], lw=0.8))

# — Chart 3: Walk-forward bars —
ax3 = axes[2]
x = range(len(wf_df))
ax3.bar([i - 0.2 for i in x], wf_df["train_ret"], width=0.38,
        color=C["ma200"], alpha=0.8, label="Train (6mo)")
ax3.bar([i + 0.2 for i in x], wf_df["test_ret"],  width=0.38,
        color=C["equity"], alpha=0.8, label="Test (3mo)")

for i, row in wf_df.iterrows():
    ax3.annotate(f"{row['train_ret']:.1f}%", xy=(i - 0.2, row["train_ret"]),
                 xytext=(0, 4), textcoords="offset points",
                 ha="center", fontsize=7, color=C["ma20"])
    ax3.annotate(f"{row['test_ret']:.1f}%",  xy=(i + 0.2, row["test_ret"]),
                 xytext=(0, 4), textcoords="offset points",
                 ha="center", fontsize=7, color=C["equity"])

ax3.set_title("Walk-Forward Analysis (6-mo train → 3-mo test)", fontsize=13, pad=10)
ax3.set_xticks(list(x))
ax3.set_xticklabels(wf_df["window"].tolist(), rotation=45, ha="right", fontsize=8)
ax3.legend(loc="upper right", framealpha=0.2)
ax3.set_ylabel("Return (%)")
ax3.axhline(0, color=C["fg"], lw=0.8, ls="--")

avg_train = wf_df["train_ret"].mean()
avg_test  = wf_df["test_ret"].mean()
ax3.annotate(f"Avg train: {avg_train:+.1f}%\nAvg test: {avg_test:+.1f}%",
             xy=(0.02, 0.97), xycoords="axes fraction",
             color=C["fg"], fontsize=9, va="top", ha="left",
             bbox=dict(boxstyle="round,pad=0.4", facecolor=C["bg"],
                       edgecolor=C["ma200"], alpha=0.6))

plt.tight_layout(pad=2.0)
plt.savefig("btc_backtest_complete.png", dpi=150, bbox_inches="tight", facecolor=C["bg"])
print("\n  → Chart saved: btc_backtest_complete.png")

# ─────────────────────────────────────────────
# 6. TRADE LOG PRINT
# ─────────────────────────────────────────────
print("\nTrade Log:")
print(f"  {'Entry':<12} {'Exit':<12} {'Entry $':>10} {'Exit $':>10} {'PnL %':>8}")
print("  " + "-"*56)
for _, t in trades_df.iterrows():
    flag = "✓" if t["pnl_pct"] > 0 else "✗"
    print(f"  {str(t['entry_date'].date()):<12} {str(t['exit_date'].date()):<12} "
          f"${t['entry_px']:>10,.0f} ${t['exit_px']:>10,.0f} {t['pnl_pct']:>+7.2f}% {flag}")

print("\nDone.")
