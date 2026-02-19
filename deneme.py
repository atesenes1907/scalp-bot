import yfinance as yf
import pandas as pd

ticker = "THYAO.IS"   # istediğin hisseyi yaz

df = yf.download(ticker, period="5d", interval="1d", progress=False)

if df.empty:
    print("Veri gelmedi.")
    exit()

last_date = df.index[-1]
last_close = df["Close"].iloc[-1]
current_time = pd.Timestamp.now()

print("Ticker:", ticker)
print("Son veri tarihi:", last_date)
print("Son kapanış fiyatı:", last_close)
print("Sistem zamanı:", current_time)

# Gün farkı hesapla
time_diff = current_time.date() - last_date.date()
print("Gün farkı:", time_diff.days, "gün")
