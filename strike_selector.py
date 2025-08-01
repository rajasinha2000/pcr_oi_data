import yfinance as yf
from datetime import datetime, timedelta

def get_upcoming_thursday():
    today = datetime.today()
    for i in range(7):
        day = today + timedelta(days=i)
        if day.weekday() == 3:  # Thursday
            return day.strftime("%d%b%y").upper()

def get_nifty_strikes():
    spot_data = yf.Ticker("^NSEI").history(period="1d")
    spot = round(spot_data['Close'].iloc[-1])
    base = int(round(spot / 50) * 50)
    expiry = get_upcoming_thursday()
    
    strikes = []
    for offset in [0]:
        strike = base + offset
        strikes.append(f"NIFTY{expiry}{strike}CE")
        strikes.append(f"NIFTY{expiry}{strike}PE")

    return {"spot": spot, "expiry": expiry, "strikes": strikes}

def get_stock_strikes(stock_symbol):
    try:
        spot = yf.Ticker(stock_symbol).history(period='1d')["Close"].iloc[-1]
        spot = round(spot, 2)
        base_strike = round(spot / 100) * 100
        expiry = get_upcoming_thursday()

        strikes = []
        for offset in [0]:
            strike = int(base_strike + offset)
            ce = f"{stock_symbol.replace('.NS', '').upper()}{expiry}{strike}CE"
            pe = f"{stock_symbol.replace('.NS', '').upper()}{expiry}{strike}PE"
            strikes.extend([ce, pe])

        return strikes
    except Exception as e:
        print(f"Error fetching stock strikes for {stock_symbol}: {e}")
        return []
