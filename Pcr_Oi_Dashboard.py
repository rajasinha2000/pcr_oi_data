import requests
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# === AUTO REFRESH ===
st_autorefresh(interval=900000, limit=None, key="option_chain_autorefresh")  # 15 mins

st.subheader("📘 Enhanced NIFTY Option Chain View (Live from NSE)")

# === EMAIL ALERT FUNCTION ===
def send_email_alert(subject, message, to_email="mdrinfotech79@gmail.com"):
    from_email = "rajasinha2000@gmail.com"
    from_password = "hefy otrq yfji ictv"  # Use app-specific password
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    try:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, from_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        st.warning(f"📧 Email alert failed: {e}")

# === FETCH OPTION CHAIN ===
def get_nifty_option_chain():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://www.nseindia.com/option-chain"
    }
    session = requests.Session()
    session.headers.update(headers)

    session.get("https://www.nseindia.com", timeout=5)
    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    response = session.get(url, timeout=10)
    data = response.json()

    records = data['records']['data']
    underlying = float(data['records']['underlyingValue'])

    rows = []
    for item in records:
        strike = item['strikePrice']
        ce = item.get('CE', {})
        pe = item.get('PE', {})
        rows.append({
            "Strike": strike,
            "CE_OI": ce.get("openInterest", 0),
            "PE_OI": pe.get("openInterest", 0),
            "Underlying": underlying
        })

    df = pd.DataFrame(rows)
    df = df[df["Strike"] % 100 == 0]
    df = df.sort_values("Strike")
    return df.reset_index(drop=True)

# === MAIN DISPLAY LOGIC ===
try:
    df_oc = get_nifty_option_chain()
    cmp = df_oc["Underlying"].iloc[0]

    # PCR calculation
    df_oc["PCR"] = (df_oc["PE_OI"] / df_oc["CE_OI"]).replace([float('inf'), -float('inf')], 0).fillna(0).round(2)

    def classify_pcr(pcr):
        if pcr > 1.2:
            return "🟢 Bullish"
        elif pcr < 0.9:
            return "🔴 Bearish"
        else:
            return "🟠 Neutral"

    df_oc["Signal"] = df_oc["PCR"].apply(classify_pcr)

    def breakout_chance(ce_oi, pe_oi):
        spread = abs(ce_oi - pe_oi)
        total = ce_oi + pe_oi
        ratio = spread / total if total != 0 else 0
        if ratio < 0.15:
            return "🔥 High"
        elif ratio < 0.3:
            return "🌥️ Medium"
        else:
            return "❄️ Low"

    df_oc["Breakout Chance"] = df_oc.apply(lambda row: breakout_chance(row["CE_OI"], row["PE_OI"]), axis=1)

    def trend_direction(signal):
        if signal == "🟢 Bullish":
            return "🔼 Uptrend"
        elif signal == "🔴 Bearish":
            return "🔽 Downtrend"
        else:
            return "🔁 Sideways"

    df_oc["Trend"] = df_oc["Signal"].apply(trend_direction)

    # === FILTER: Only keep latest row per Strike ===
    df_oc = df_oc.sort_values(by=["Strike"], ascending=True).drop_duplicates(subset="Strike", keep="last")

    # Focus on strikes around current market price (CMP)
    above_cmp = df_oc[df_oc["Strike"] >= cmp].head(5)
    below_cmp = df_oc[df_oc["Strike"] < cmp].tail(5)
    df_filtered = pd.concat([below_cmp, above_cmp]).sort_values("Strike")

    # Show filtered and clean table
    display_cols = ["Strike", "CE_OI", "PE_OI", "PCR", "Signal", "Breakout Chance", "Trend"]
    st.dataframe(df_filtered[display_cols], use_container_width=True)


    display_cols = ["Strike", "CE_OI", "PE_OI", "PCR", "Signal", "Breakout Chance", "Trend"]
    

    # Summary
    max_ce = df_oc.loc[df_oc["CE_OI"].idxmax(), "Strike"]
    max_pe = df_oc.loc[df_oc["PE_OI"].idxmax(), "Strike"]
    total_pcr = round(df_oc["PE_OI"].sum() / df_oc["CE_OI"].sum(), 2)

    sentiment = "🟢 Bullish" if total_pcr > 1.2 else "🔴 Bearish" if total_pcr < 0.8 else "🟠 Neutral"

    st.markdown(f"""
    ### 🧭 Option Chain Summary:
    - 🔼 **Max CE OI (Resistance)**: `{max_ce}`
    - 🔽 **Max PE OI (Support)**: `{max_pe}`
    - ⚖️ **Total PCR**: `{total_pcr}` → {sentiment}
    - 📍 **Current Price**: `{cmp}`
    """)

    # === EMAIL ALERT TRIGGER ===
    if total_pcr > 1.2:
        send_email_alert(
            "📈 Bullish Option Chain Signal",
            f"Total PCR: {total_pcr} indicates a strong bullish bias.\nMax CE OI: {max_ce}, Max PE OI: {max_pe}, CMP: {cmp}"
        )
    elif total_pcr < 0.8:
        send_email_alert(
            "📉 Bearish Option Chain Signal",
            f"Total PCR: {total_pcr} indicates a strong bearish bias.\nMax CE OI: {max_ce}, Max PE OI: {max_pe}, CMP: {cmp}"
        )

except Exception as e:
    st.error(f"Error fetching option chain: {e}")
