import yfinance as yf
import pandas as pd
import ta
import numpy as np

# ==========================
# AYARLAR
# ==========================
INTERVAL = "15m"
PERIOD = "5d"
TP_PERCENT = 0.025
ATR_MULTIPLIER = 1.2
MIN_VOLUME_RATIO = 1.5

bist_df = pd.read_csv("bist_list.csv")
tickers = [x + ".IS" for x in bist_df["Ticker"].tolist()]

results = []

for ticker in tickers:
    try:
        df = yf.download(ticker, period=PERIOD, interval=INTERVAL, progress=False)

        if df.empty or len(df) < 50:
            continue

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        atr = ta.volatility.average_true_range(high, low, close, window=14)
        vol_ma20 = volume.rolling(20).mean()

        df = df.assign(atr=atr, vol_ma20=vol_ma20).dropna()

        last = df.iloc[-1]

        # ==========================
        # HACİM PATLAMASI
        # ==========================
        volume_ratio = last.Volume / last.vol_ma20
        if volume_ratio < MIN_VOLUME_RATIO:
            continue

        # ==========================
        # İLK SAAT RANGE BREAKOUT
        # ==========================
        first_hour = df.iloc[:4]  # 15m x 4 = 1 saat
        first_hour_high = first_hour["High"].max()

        if last.Close <= first_hour_high:
            continue

        # ==========================
        # ATR POTANSİYELİ
        # ==========================
        atr_percent = last.atr / last.Close * 100
        if atr_percent < 0.8:
            continue

        entry = last.Close
        stop = entry - ATR_MULTIPLIER * last.atr
        target = entry * (1 + TP_PERCENT)

        risk = entry - stop
        reward = target - entry

        if risk <= 0:
            continue

        rr = reward / risk

        if rr < 1.2:
            continue

        score = atr_percent * 10 + volume_ratio * 5

        results.append({
            "Ticker": ticker,
            "Score": round(score, 2),
            "Entry": round(entry, 2),
            "Target(%2.5)": round(target, 2),
            "Stop": round(stop, 2),
            "RR": round(rr, 2),
            "VolRatio": round(volume_ratio, 2)
        })

    except:
        continue


results_df = pd.DataFrame(results)

if results_df.empty:
    print("\n⚠️ Intraday scalp için uygun hisse yok.")
else:
    results_df = results_df.sort_values("Score", ascending=False)
    print("\n🔥 INTRADAY SCALP FIRSATLARI\n")
    print(results_df.head(10).to_string(index=False))
