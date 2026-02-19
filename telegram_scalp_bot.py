import yfinance as yf
import pandas as pd
import ta
import numpy as np
import requests
import time

# ==========================
# TELEGRAM AYARLARI
# ==========================
TOKEN = "AAHoeBQMPKx_LYeFTZRL-zHaugQDrBS0K48"
CHAT_ID = "6098301795"

# ==========================
# STRATEJİ AYARLARI
# ==========================
INTERVAL = "15m"
PERIOD = "5d"
TP_PERCENT = 0.025
ATR_MULTIPLIER = 1.2
MIN_VOLUME_RATIO = 1.5

# ==========================
# TELEGRAM MESAJ FONKSİYONU
# ==========================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=data)

# ==========================
# HİSSE LİSTESİ
# ==========================
bist_df = pd.read_csv("bist_list.csv")
tickers = [x + ".IS" for x in bist_df["Ticker"].tolist()]

print("🔍 Tarama başlıyor...")

signals = []

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

        atr = ta.volatility.average_true_range(high, low, close, 14)
        vol_ma20 = volume.rolling(20).mean()

        df = df.assign(atr=atr, vol_ma20=vol_ma20).dropna()
        last = df.iloc[-1]

        # HACİM PATLAMASI
        volume_ratio = last.Volume / last.vol_ma20
        if volume_ratio < MIN_VOLUME_RATIO:
            continue

        # İLK SAAT RANGE
        first_hour = df.iloc[:4]
        first_hour_high = first_hour["High"].max()

        if last.Close <= first_hour_high:
            continue

        # ATR %
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

        message = f"""
🔥 INTRADAY SCALP SİNYALİ

Hisse: {ticker}
Entry: {round(entry,2)}
Target: {round(target,2)}
Stop: {round(stop,2)}
RR: {round(rr,2)}
VolRatio: {round(volume_ratio,2)}
ATR%: {round(atr_percent,2)}
"""

        signals.append(message)

    except:
        continue

# ==========================
# MESAJ GÖNDER
# ==========================
if signals:
    for s in signals:
        send_telegram(s)
        time.sleep(1)
    print("✅ Sinyaller gönderildi.")
else:
    print("⚠️ Sinyal yok.")
