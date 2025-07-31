
from indicator_utils import rsi

def analyze_trend(df, symbol):
    if df is None or df.empty or 'Close' not in df.columns:
        return {"is_bullish": False, "reason": "No data"}

    df['RSI'] = rsi(df)
    df['EMA20'] = df['Close'].ewm(span=20).mean()

    latest_close = float(df['Close'].iloc[-1])
    latest_ema = float(df['EMA20'].iloc[-1])
    latest_rsi = float(df['RSI'].iloc[-1])

    # Default for stocks or unknown symbols
    is_bullish = latest_close > latest_ema and latest_rsi > 50
    reason = "Bullish if Close > EMA20 and RSI > 50"

    # For Call Options
    if "CE" in symbol:
        is_bullish = latest_close > latest_ema and latest_rsi > 50
        reason = "CE Bullish if Close > EMA20 and RSI > 50"

    # For Put Options
    elif "PE" in symbol:
        is_bullish = latest_close < latest_ema and latest_rsi < 50
        reason = "PE Bullish if Close < EMA20 and RSI < 50"

    return {
        "is_bullish": is_bullish,
        "rsi": round(latest_rsi, 2),
        "ema": round(latest_ema, 2),
        "close": round(latest_close, 2),
        "reason": reason
    }
