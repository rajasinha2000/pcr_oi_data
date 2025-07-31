import streamlit as st
import pandas as pd
import time

from strike_selector import get_nifty_strikes
from fetch_candles import get_option_candles
from analyze import analyze_trend
from telegram_utils import send_telegram_alert

st.set_page_config(page_title="NIFTY Option Monitor", layout="wide")
st.title("📊 NIFTY Option Signal Monitor (ATM ±2)")

refresh_interval = st.sidebar.slider("Refresh Interval (sec)", 30, 300, 60, step=30)
run_monitor = st.sidebar.button("🔁 Refresh Now")
reset_alerts = st.sidebar.button("🔄 Reset Alerts")

# Initialize alert memory
if "alerted" not in st.session_state:
    st.session_state.alerted = set()

if reset_alerts:
    st.session_state.alerted.clear()
    st.success("✅ Alert list reset.")

def display_table():
    result_rows = []

    data = get_nifty_strikes()
    spot = data["spot"]
    expiry = data["expiry"]
    strikes = data["strikes"]

    st.markdown(f"**NIFTY Spot:** `{spot}` | **Expiry:** `{expiry}`")

    for symbol in strikes:
        candles = get_option_candles(symbol)
        if not candles or '5m' not in candles or '15m' not in candles:
            continue

        tf5 = analyze_trend(candles['5m'], symbol)
        tf15 = analyze_trend(candles['15m'], symbol)

        if not isinstance(tf5, dict) or not isinstance(tf15, dict):
            st.warning(f"Invalid trend data for {symbol}")
            continue

        is_bullish_both = tf5['is_bullish'] and tf15['is_bullish']

        row = {
            "Option": symbol,
            "5m RSI": tf5['rsi'],
            "5m EMA": tf5['ema'],
            "5m Close": tf5['close'],
            "15m RSI": tf15['rsi'],
            "15m EMA": tf15['ema'],
            "15m Close": tf15['close'],
            "Bullish?": "✅" if is_bullish_both else "❌"
        }
        result_rows.append(row)

        if is_bullish_both and symbol not in st.session_state.alerted:
            message = (
                f"🚀 *NIFTY Option Alert* `{symbol}`\n"
                f"✅ *Bullish on 5m & 15m*\n\n"
                f"*5m* → RSI: `{tf5['rsi']}`, EMA: `{tf5['ema']}`, Close: `{tf5['close']}`\n"
                f"*15m* → RSI: `{tf15['rsi']}`, EMA: `{tf15['ema']}`, Close: `{tf15['close']}`"
            )
            send_telegram_alert(message)
            st.session_state.alerted.add(symbol)
            st.toast(f"🚨 Alert sent: {symbol}", icon="🚀")

    # Display table
    df = pd.DataFrame(result_rows)
    if not df.empty:
        st.dataframe(df.style.apply(
            lambda row: ['background-color: lightgreen' if row["Bullish?"] == "✅" else '' for _ in row],
            axis=1
        ), use_container_width=True)
    else:
        st.warning("⚠️ No data to display.")

# Manual run
if run_monitor:
    display_table()

# Auto-refresh every N seconds
st_autorefresh = st.empty()
while True:
    time.sleep(refresh_interval)
    with st_autorefresh.container():
        display_table()
