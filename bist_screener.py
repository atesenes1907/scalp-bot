import yfinance as yf
import pandas as pd
import string

valid_tickers = []

# 4 harfli kombinasyon brute force (A-Z)
letters = string.ascii_uppercase

for a in letters:
    for b in letters:
        for c in letters:
            for d in letters:
                symbol = f"{a}{b}{c}{d}.IS"
                try:
                    df = yf.download(symbol, period="5d", progress=False)
                    if not df.empty:
                        valid_tickers.append(symbol.replace(".IS", ""))
                        print("Bulundu:", symbol)
                except:
                    continue

# CSV kaydet
pd.DataFrame({"Ticker": valid_tickers}).to_csv("bist_list.csv", index=False)

print("Toplam bulunan:", len(valid_tickers))
