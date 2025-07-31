from datetime import date, timedelta
import yfinance as yf
import math

def get_nifty_strikes():
    nifty = yf.Ticker("^NSEI")
    spot = nifty.history(period="1d")["Close"].iloc[-1]
    atm = int(round(spot / 50.0)) * 50

    expiry = get_upcoming_thursday()

    strikes = []
    for offset in [0]:
        strike = atm + offset
        strikes.append(f"NIFTY{expiry}{strike}CE")
        strikes.append(f"NIFTY{expiry}{strike}PE")

    # ✅ Add stocks here
    stocks = ["HDFCBANK.NS","TCS.NS", "RELIANCE.NS","LT.NS","BHARTIARTL.NS","MARUTI.NS","ULTRACEMCO.NS","HAL.NS"]
    strikes.extend(stocks)

    return {
        "spot": round(spot, 2),
        "expiry": expiry,
        "strikes": strikes
    }

def get_upcoming_thursday():
    today = date.today()
    offset = (3 - today.weekday()) % 7  # 3 = Thursday
    expiry = today + timedelta(days=offset)
    return expiry.strftime("%d%b%y").upper()
