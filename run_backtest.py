import requests, pandas as pd, matplotlib.pyplot as plt

url = "https://api.binance.com/api/v3/klines"
resp = requests.get(url, params={"symbol":"BTCUSDT","interval":"1d","limit":1000})
df = pd.DataFrame(resp.json(), columns=["ot","open","high","low","close","vol","ct","qv","tr","tbv","tbqv","ign"])
df["date"] = pd.to_datetime(pd.to_numeric(df["ot"]), unit="ms")
df.set_index("date", inplace=True)
for c in ["open","high","low","close","vol"]: df[c] = pd.to_numeric(df[c])

df["ma20"]   = df["close"].rolling(20).mean()
df["ma200"]  = df["close"].rolling(200).mean()
df["signal"] = (df["ma20"] > df["ma200"]).astype(int)
df["vol_ma7"]= df["vol"].rolling(7).mean()

df.to_csv("btc_price_data.csv")

btc = df[df["ma200"].notna()].copy()
btc["position"]         = btc["signal"].replace(0, -1)
btc["daily_return"]     = btc["close"].pct_change()
btc["strategy_return"]  = btc["daily_return"] * btc["position"].shift(1)
btc["equity"]           = (1 + btc["strategy_return"]).cumprod()
btc["btc_equity"]       = (1 + btc["daily_return"]).cumprod()
btc["entry_signal"]     = (btc["signal"]==1) & (btc["signal"].shift(1)==0)
btc["exit_signal"]      = (btc["signal"]==0) & (btc["signal"].shift(1)==1)

print(f"Backtest: {btc.index[0].date()} -> {btc.index[-1].date()} ({len(btc)} days)")
trades = btc[btc["entry_signal"]|btc["exit_signal"]].copy()
trades["action"] = trades.apply(lambda r: "BUY" if r["entry_signal"] else "SELL", axis=1)
print(f"Trades: {len(trades)}")
print(trades[["close","signal","action"]].to_string())

start, end = btc["close"].iloc[0], btc["close"].iloc[-1]
n = len(btc)/365
print(f"\nStrategy return: {(btc['equity'].iloc[-1]-1)*100:.2f}%  (BTC: {(end/start-1)*100:.2f}%)")
print(f"Strategy ann:    {((btc['equity'].iloc[-1]**(1/n)-1)*100):.2f}%  (BTC:  {((end/start)**(1/n)-1)*100:.2f}%)")
dd = (btc["equity"]-btc["equity"].cummax())/btc["equity"].cummax()
print(f"Max drawdown:   {dd.min()*100:.2f}%")

fig,axes = plt.subplots(3,1,figsize=(14,12))
ax1=axes[0]; ax2=axes[1]; ax3=axes[2]
ax1.plot(btc.index, btc["btc_equity"], "--", color="gray",  lw=0.8, label="BTC Buy & Hold")
ax1.plot(btc.index, btc["equity"],     color="blue",  lw=1.2, label="MA Crossover Strategy")
ax1.set_ylabel("Portfolio Value ($)"); ax1.set_title("Equity Curve"); ax1.legend(); ax1.grid(alpha=0.3)
ax2.fill_between(btc.index, dd*100, 0, color="red", alpha=0.3, label="Drawdown")
ax2.plot(btc.index, dd*100, color="red", lw=0.5); ax2.set_ylabel("Drawdown (%)"); ax2.legend(); ax2.grid(alpha=0.3)
ax3.plot(btc.index, btc["close"],  color="black", lw=0.8, label="BTC Close")
ax3.plot(btc.index, btc["ma20"],  color="blue",  lw=0.6, label="MA20", alpha=0.7)
ax3.plot(btc.index, btc["ma200"], color="red",   lw=0.6, label="MA200", alpha=0.7)
for _, row in btc[btc["entry_signal"]].iterrows(): ax3.scatter(row.name, row["close"], color="green", marker="^", s=60, zorder=5)
for _, row in btc[btc["exit_signal"]].iterrows(): ax3.scatter(row.name, row["close"], color="red", marker="v", s=60, zorder=5)
ax3.scatter(btc.index[0], btc["close"].iloc[0], color="green", marker="^", s=100, zorder=6, edgecolors="yellow", linewidths=2, label="First LONG")
ax3.legend(); ax3.set_ylabel("USD"); ax3.grid(alpha=0.3)
plt.tight_layout(); plt.savefig("equity_curve.png", dpi=150); plt.show()
print("Charts saved.")
