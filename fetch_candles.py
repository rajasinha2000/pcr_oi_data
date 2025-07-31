
import yfinance as yf

def get_option_candles(symbol):
    # Use NIFTY index as proxy for trend
    spot_symbol = "^NSEI"
    try:
        df_5m = yf.download(spot_symbol, interval='5m', period='1d', progress=False)
        df_15m = yf.download(spot_symbol, interval='15m', period='5d', progress=False)
        return {"5m": df_5m, "15m": df_15m}
    except Exception as e:
        print(f"Error fetching data for {spot_symbol}: {e}")
        return {"5m": None, "15m": None}
