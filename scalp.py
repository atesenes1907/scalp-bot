import yfinance as yf
import pandas as pd
import numpy as np
import ta

# ==============================
# AYARLAR
# ==============================
PERIOD = "6mo"
MIN_AVG_VOLUME = 5_000_000
TP_PERCENT = 0.03
ATR_MULTIPLIER = 1.2
MIN_RR = 1.2

# ==============================
# HİSSE LİSTESİ
# ==============================
bist_df = pd.read_csv("bist_list.csv")
tickers = [x + ".IS" for x in bist_df["Ticker"].tolist()]

results = []

for ticker in tickers:
    try:
        df = yf.download(ticker, period=PERIOD, interval="1d", progress=False)
        if df.empty or len(df) < 60:
            continue

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        # Göstergeler
        ema20 = ta.trend.ema_indicator(close, 20)
        ema50 = ta.trend.ema_indicator(close, 50)
        rsi = ta.momentum.rsi(close, 14)
        atr = ta.volatility.average_true_range(high, low, close, 14)
        vol_ma20 = volume.rolling(20).mean()

        df = df.assign(
            ema20=ema20,
            ema50=ema50,
            rsi=rsi,
            atr=atr,
            vol_ma20=vol_ma20
        ).dropna()

        last = df.iloc[-1]

        # ==========================
        # FİLTRELER (Optimize)
        # ==========================

        # Likidite
        if last.vol_ma20 < MIN_AVG_VOLUME:
            continue

        # Trend (çok sert değil)
        if last.ema20 < last.ema50 * 0.98:
            continue

        # RSI esnek
        if not (50 <= last.rsi <= 80):
            continue

        # ATR %
        atr_percent = last.atr / last.Close * 100
        if atr_percent < 1.8:
            continue

        # 5 Günlük breakout
        recent_high = high.rolling(5).max().iloc[-2]
        if last.Close < recent_high * 0.99:
            continue

        # Hacim artışı
        volume_ratio = last.Volume / last.vol_ma20
        if volume_ratio < 1.2:
            continue

        # ==========================
        # RİSK YÖNETİMİ
        # ==========================
        entry = last.Close
        stop = entry - ATR_MULTIPLIER * last.atr
        target = entry * (1 + TP_PERCENT)

        risk = entry - stop
        reward = target - entry

        if risk <= 0:
            continue

        rr = reward / risk

        if rr < MIN_RR:
            continue

        # ==========================
        # SKOR (Momentum Ağırlıklı)
        # ==========================
        score = (
            atr_percent * 5 +
            volume_ratio * 8 +
            max((last.Close - recent_high) / recent_high * 100, 0) * 6
        )

        results.append({
            "Ticker": ticker,
            "Score": round(score, 2),
            "Entry": round(entry, 2),
            "Target(%3)": round(target, 2),
            "Stop(ATR)": round(stop, 2),
            "RR": round(rr, 2),
            "ATR%": round(atr_percent, 2),
            "VolRatio": round(volume_ratio, 2)
        })

    except Exception:
        continue


# ==========================
# SONUÇ
# ==========================
results_df = pd.DataFrame(results)

if results_df.empty:
    print("\n⚠️ Bugün scalp için uygun hisse bulunamadı.")
else:
    results_df = results_df.sort_values("Score", ascending=False)
    print("\n🔥 SCALP SİSTEMİ – EN GÜÇLÜ 10\n")
    print(results_df.head(10).to_string(index=False))
