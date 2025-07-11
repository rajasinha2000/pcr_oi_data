import streamlit as st
import pandas as pd
import requests
import numpy as np
import plotly.graph_objects as go
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# ========== PAGE CONFIG ==========
st.set_page_config(page_title="PCR + OI Dashboard", layout="wide")
st_autorefresh(interval=5 * 60 * 1000, key="refresh")
st.title("📊 PCR + OI Dashboard (Live Data)")
st.caption("Auto-refreshes every 5 minutes")

# ========== SESSION STATE ==========
if "pcr_email_sent" not in st.session_state:
    st.session_state.pcr_email_sent = {}

# ========== STOCKS & INDICES ==========
symbols = {
    "NIFTY": True,
    "BANKNIFTY": True,
    "RELIANCE": False,
    "HDFCBANK": False,
}

# ========== EMAIL CONFIG ==========
sender_email = "rajasinha2000@gmail.com"
receiver_email = "mdrinfotech79@gmail.com"
app_password = "hefy otrq yfji ictv"  # 🔐 App password

# ========== FETCH DATA FUNCTION ==========
def fetch_option_chain(symbol, is_index=True):
    url = f"https://www.nseindia.com/api/option-chain-{'indices' if is_index else 'equities'}?symbol={symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://www.nseindia.com",
    }
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)
    res = session.get(url, headers=headers)
    return res.json()

# ========== EMAIL ALERT ==========
def send_pcr_email_alert(symbol, pcr, bias):
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

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
    except Exception as e:
        st.error(f"❌ Email failed for {symbol}: {e}")

# ========== PCR LOGIC ==========
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
        s_shift = "↔"
        r_shift = "↔"

        if pcr >= 1.3:
            trend = "🔼"
            bias = "⚠️ Overbought Watch"
        elif pcr <= 0.8:
            trend = "🔽"
            bias = "🟢 Oversold Bias"
        else:
            trend = "↔"
            bias = "⚪ Neutral Bias"

        return {
            "Symbol": symbol,
            "PCR": pcr,
            "Trend": trend,
            "Bias": bias,
            "Support": support_strike,
            "S-Shift": s_shift,
            "PUT OI Chg": f"{int(pe_oi_change.get(support_strike, 0) / 1000)}K",
            "Resistance": resistance_strike,
            "R-Shift": r_shift,
            "CALL OI Chg": f"{int(ce_oi_change.get(resistance_strike, 0) / 1000)}K",
        }

    except Exception as e:
        return {
            "Symbol": symbol,
            "PCR": "-",
            "Trend": "-",
            "Bias": f"Error: {str(e)}",
            "Support": "-",
            "S-Shift": "-",
            "PUT OI Chg": "-",
            "Resistance": "-",
            "R-Shift": "-",
            "CALL OI Chg": "-",
        }

# ========== PROCESS ALL SYMBOLS ==========
data = []

for symbol, is_index in symbols.items():
    row = analyze_symbol(symbol, is_index)

    if isinstance(row["PCR"], (float, int)):
        out_of_range = row["PCR"] > 1.3 or row["PCR"] < 0.8
        already_sent = st.session_state.pcr_email_sent.get(symbol, False)

        if out_of_range and not already_sent:
            send_pcr_email_alert(row["Symbol"], row["PCR"], row["Bias"])
            st.session_state.pcr_email_sent[symbol] = True

        elif not out_of_range:
            st.session_state.pcr_email_sent[symbol] = False

    data.append(row)

df = pd.DataFrame(data)

# ========== PCR STYLE ==========
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

# ========== DISPLAY TABLE ==========
st.dataframe(styled_df, use_container_width=True)

# ========== PCR ALERT DISPLAY ==========
for _, row in df.iterrows():
    if isinstance(row["PCR"], (float, int)):
        if row["PCR"] > 1.3:
            st.warning(f"⚠️ {row['Symbol']} is Overbought (PCR={row['PCR']})")
        elif row["PCR"] < 0.8:
            st.success(f"🟢 {row['Symbol']} is Oversold (PCR={row['PCR']})")

# ========== OPTIONAL EMAIL STATUS ==========
with st.expander("📨 Email Alert Status"):
    for symbol, sent in st.session_state.pcr_email_sent.items():
        if sent:
            st.markdown(f"✅ Email alert already sent for **{symbol}**", unsafe_allow_html=True)

# ========== EXPORT CSV ==========
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download CSV", csv, "pcr_oi_dashboard.csv", "text/csv")

# ========== OI CHART ==========
selected_symbol = st.selectbox("📌 View OI Chart for", df["Symbol"])
if selected_symbol and selected_symbol in symbols:
    try:
        is_index = symbols[selected_symbol]
        data = fetch_option_chain(selected_symbol, is_index)
        records = data['records']['data']

        oi_chart_data = []
        for entry in records:
            strike = entry.get("strikePrice")
            ce_oi = entry.get("CE", {}).get("openInterest", 0)
            pe_oi = entry.get("PE", {}).get("openInterest", 0)
            oi_chart_data.append((strike, ce_oi, pe_oi))

        chart_df = pd.DataFrame(oi_chart_data, columns=["Strike", "CE_OI", "PE_OI"]).sort_values("Strike")
        fig = go.Figure(data=[
            go.Bar(name="Call OI", x=chart_df["Strike"], y=chart_df["CE_OI"], marker_color="red"),
            go.Bar(name="Put OI", x=chart_df["Strike"], y=chart_df["PE_OI"], marker_color="green")
        ])
        fig.update_layout(barmode="group", title=f"{selected_symbol} Open Interest by Strike", xaxis_title="Strike Price", yaxis_title="Open Interest")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Chart Error: {e}")

# ========== FOOTER ==========
st.markdown("---")
st.markdown("Built with ❤️ by MDR — Live PCR, Support/Resistance, OI Analysis")
