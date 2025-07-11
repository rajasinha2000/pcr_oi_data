import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import time
from streamlit_autorefresh import st_autorefresh

# ========== CONFIG ==========
st.set_page_config(page_title="PCR + OI Dashboard", layout="wide")
st.title("📊 PCR + OI Dashboard (Live)")
st.caption("Auto-refresh every 5 minutes")

# Auto-refresh every 5 minutes (300000 ms)
st_autorefresh(interval=300000, key="refresh")

# ========== EMAIL CONFIG ==========
sender_email = "rajasinha2000@gmail.com"
receiver_email = "mdrinfotech79@gmail.com"
app_password = "hefy otrq yfji ictv"

# ========== SESSION STATE ==========
if "last_alerts" not in st.session_state:
    st.session_state.last_alerts = {}

# ========== DEFAULT SYMBOLS ==========
fixed_symbols = {"NIFTY": True,"BANKNIFTY": True,"RELIANCE": False,}
user_symbols = st.session_state.get("user_symbols", set())

with st.sidebar:
    st.markdown("### ➕ Add/Remove Symbols")
    new_symbol = st.text_input("Add F&O Stock (e.g., RELIANCE)", "")
    if st.button("Add Symbol") and new_symbol.strip():
        user_symbols.add(new_symbol.strip().upper())
        st.session_state.user_symbols = user_symbols

    remove_symbol = st.selectbox("Remove Symbol", sorted(user_symbols))
    if st.button("Remove Symbol"):
        user_symbols.discard(remove_symbol)
        st.session_state.user_symbols = user_symbols

all_symbols = {**fixed_symbols, **{sym: False for sym in user_symbols}}

# ========== FETCH FUNCTION ==========
def fetch_option_chain(symbol, is_index=True):
    try:
        url = f"https://www.nseindia.com/api/option-chain-{'indices' if is_index else 'equities'}?symbol={symbol}"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": "https://www.nseindia.com"
        }
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        response = session.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Invalid response received from NSE")
    except Exception as e:
        raise Exception("Fetch failed for {}: {}".format(symbol, e))

# ========== EMAIL ALERT ==========
def send_pcr_email_alert(symbol, pcr, bias):
    try:
        subject = f"{symbol} PCR Alert: {bias}"
        body = f"""
        PCR Alert for {symbol}
        -----------------------
        PCR Value: {pcr}
        Bias: {bias}

        Link: https://www.nseindia.com/option-chain

        - MDR PCR Dashboard
        """
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
    except:
        pass

# ========== PCR ANALYSIS ==========
def analyze_symbol(symbol, is_index):
    try:
        data = fetch_option_chain(symbol, is_index)
        records = data['records']['data']

        ce_oi_total = 0
        pe_oi_total = 0
        ce_oi_change = {}
        pe_oi_change = {}
        ce_strike = {}
        pe_strike = {}

        for entry in records:
            strike = entry.get("strikePrice")
            if "CE" in entry:
                ce = entry["CE"]
                ce_oi_total += ce.get("openInterest", 0)
                ce_oi_change[strike] = ce.get("changeinOpenInterest", 0)
                ce_strike[strike] = ce.get("openInterest", 0)
            if "PE" in entry:
                pe = entry["PE"]
                pe_oi_total += pe.get("openInterest", 0)
                pe_oi_change[strike] = pe.get("changeinOpenInterest", 0)
                pe_strike[strike] = pe.get("openInterest", 0)

        pcr = round(pe_oi_total / ce_oi_total, 2) if ce_oi_total else 0
        support_strike = max(pe_strike, key=pe_strike.get)
        resistance_strike = max(ce_strike, key=ce_strike.get)

        if pcr >= 1.3:
            trend = "🔼"
            bias = "⚠️ Overbought Watch"
        elif pcr <= 0.8:
            trend = "🔽"
            bias = "🟢 Oversold Bias"
        else:
            trend = "↔"
            bias = "⚪ Neutral Bias"

        # Send alert only on bias change
        if symbol not in st.session_state.last_alerts or st.session_state.last_alerts[symbol] != bias:
            if pcr >= 1.3 or pcr <= 0.8:
                send_pcr_email_alert(symbol, pcr, bias)
            st.session_state.last_alerts[symbol] = bias

        return {
            "Symbol": symbol,
            "PCR": pcr,
            "Trend": trend,
            "Bias": bias,
            "Support": support_strike,
            "S-Shift": "↔",
            "PUT OI Chg": f"{int(pe_oi_change.get(support_strike, 0)/1000)}K",
            "Resistance": resistance_strike,
            "R-Shift": "↔",
            "CALL OI Chg": f"{int(ce_oi_change.get(resistance_strike, 0)/1000)}K",
        }
    except Exception as e:
        return {
            "Symbol": symbol,
            "PCR": "-",
            "Trend": "-",
            "Bias": f"Error: {e}",
            "Support": "-", "S-Shift": "-", "PUT OI Chg": "-",
            "Resistance": "-", "R-Shift": "-", "CALL OI Chg": "-"
        }

# ========== ANALYZE ALL SYMBOLS ==========
results = []
for symbol, is_index in all_symbols.items():
    results.append(analyze_symbol(symbol, is_index))

df = pd.DataFrame(results)

# ========== STYLE ==========
def pcr_style(val):
    try:
        val = float(val)
        if val >= 1.3:
            return "background-color: #2f855a; color: white; font-weight: bold;"
        elif val <= 0.8:
            return "background-color: #c53030; color: white; font-weight: bold;"
        else:
            return "background-color: #faf089; color: black; font-weight: bold;"
    except:
        return ""

styled_df = df.style.applymap(pcr_style, subset=["PCR"])
st.dataframe(styled_df, use_container_width=True)

# ========== DOWNLOAD ==========
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download CSV", csv, "pcr_oi_dashboard.csv", "text/csv")

# ========== OI CHART ==========
selected_symbol = st.selectbox("📌 View OI Chart for", df["Symbol"])
if selected_symbol in all_symbols:
    try:
        is_index = all_symbols[selected_symbol]
        data = fetch_option_chain(selected_symbol, is_index)
        records = data['records']['data']

        strikes = []
        ce_oi = []
        pe_oi = []

        for entry in records:
            strike = entry.get("strikePrice")
            ce = entry.get("CE", {}).get("openInterest", 0)
            pe = entry.get("PE", {}).get("openInterest", 0)
            if ce > 0 or pe > 0:
                strikes.append(strike)
                ce_oi.append(ce)
                pe_oi.append(pe)

        df_oi = pd.DataFrame({"Strike": strikes, "CE": ce_oi, "PE": pe_oi}).sort_values("Strike")
        atm_index = df_oi["PE"].idxmax()
        chart_df = df_oi.iloc[max(0, atm_index - 5): atm_index + 5]

        fig = go.Figure(data=[
            go.Bar(name="Call OI", x=chart_df["Strike"], y=chart_df["CE"], marker_color="red"),
            go.Bar(name="Put OI", x=chart_df["Strike"], y=chart_df["PE"], marker_color="green")
        ])
        fig.update_layout(
            barmode="group",
            title=f"{selected_symbol} OI Chart (Top 10 strikes)",
            xaxis_title="Strike Price", yaxis_title="Open Interest"
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Chart Error: {e}")

# ========== FOOTER ==========
st.markdown("---")
st.markdown("Built with ❤️ by MDR — Live PCR, Support/Resistance, OI Analysis")
