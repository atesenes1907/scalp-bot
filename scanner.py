import yfinance as yf
import pandas as pd
import numpy as np
import ta

# ================================
# AYARLAR
# ================================
MIN_AVG_VOLUME = 5_000_000   # Minimum 20 günlük ortalama hacim
PERIOD = "6mo"

# ================================
# HİSSE LİSTESİ
# ================================
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

        close = df["Close"].squeeze()
        high = df["High"].squeeze()
        low = df["Low"].squeeze()
        volume = df["Volume"].squeeze()
        openp = df["Open"].squeeze()

        # Teknikler
        ema20 = ta.trend.ema_indicator(close, window=20)
        ema50 = ta.trend.ema_indicator(close, window=50)
        rsi = ta.momentum.rsi(close, window=14)
        atr = ta.volatility.average_true_range(high, low, close, window=14)
        vol_ma20 = volume.rolling(20).mean()

        # Son değerler
        last_close = close.iloc[-1]
        last_open = openp.iloc[-1]
        last_volume = volume.iloc[-1]
        last_rsi = rsi.iloc[-1]
        last_ema20 = ema20.iloc[-1]
        last_ema50 = ema50.iloc[-1]
        last_atr = atr.iloc[-1]
        last_vol_ma20 = vol_ma20.iloc[-1]

        # ================================
        # LİKİDİTE FİLTRESİ
        # ================================
        if last_vol_ma20 < MIN_AVG_VOLUME:
            continue

        score = 0

        # ================================
        # 1️⃣ TREND GÜCÜ (max 20)
        # ================================
        trend_strength = (last_ema20 - last_ema50) / last_ema50 * 100
        if trend_strength > 0:
            score += min(trend_strength * 5, 20)

        # ================================
        # 2️⃣ RSI MOMENTUM (max 15)
        # ================================
        if 50 <= last_rsi <= 70:
            score += (last_rsi - 50) * 0.75

        # ================================
        # 3️⃣ BREAKOUT GÜCÜ (max 20)
        # ================================
        recent_high = high.rolling(5).max().iloc[-2]
        breakout_strength = (last_close - recent_high) / recent_high * 100
        if breakout_strength > 0:
            score += min(breakout_strength * 10, 20)

        # ================================
        # 4️⃣ HACİM GÜCÜ (max 20)
        # ================================
        volume_ratio = last_volume / last_vol_ma20
        if volume_ratio > 1:
            score += min(volume_ratio * 10, 20)

        # ================================
        # 5️⃣ ATR GENİŞLEME (max 15)
        # ================================
        atr_mean = atr.rolling(20).mean().iloc[-1]
        if last_atr > atr_mean:
            atr_ratio = last_atr / atr_mean
            score += min(atr_ratio * 7, 15)

        # ================================
        # 6️⃣ GÜÇLÜ MUM (max 10)
        # ================================
        daily_change = (last_close - last_open) / last_open * 100
        if daily_change > 0:
            score += min(daily_change * 2, 10)

        results.append((ticker, round(score, 2)))

    except Exception as e:
        print(f"Hata: {ticker} - {e}")
        continue


# ================================
# SIRALA
# ================================
results = sorted(results, key=lambda x: x[1], reverse=True)

print("\n📊 En Güçlü 5 Hisse:\n")

for r in results[:5]:
    print(f"{r[0]}  |  Score: {r[1]}")
