import pandas as pd

def rsi(df, period=14):
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # Flatten in case gain/loss are accidentally 2D
    if hasattr(gain, 'shape') and len(gain.shape) > 1:
        gain = gain.iloc[:, 0]
    if hasattr(loss, 'shape') and len(loss.shape) > 1:
        loss = loss.iloc[:, 0]

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi
