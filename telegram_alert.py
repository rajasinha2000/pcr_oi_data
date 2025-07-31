import requests
from config import BOT_TOKEN, CHAT_ID

def send_telegram_alert(symbol, tf5_details, tf15_details):
    msg = f"""🚀 *Bullish Alert!*

Option: `{symbol}`  
✅ 5m & 15m timeframes *both* bullish

📊 Indicators:
*5m:*  
- RSI: {tf5_details['RSI']}
- EMA20: {tf5_details['EMA20']}
- Close: {tf5_details['Close']}
- ADX: {tf5_details['ADX']}
- +DI/-DI: {tf5_details['+DI']}/{tf5_details['-DI']}
- Supertrend: {tf5_details['Supertrend']}

*15m:*  
- RSI: {tf15_details['RSI']}
- EMA20: {tf15_details['EMA20']}
- Close: {tf15_details['Close']}
- ADX: {tf15_details['ADX']}
- +DI/-DI: {tf15_details['+DI']}/{tf15_details['-DI']}
- Supertrend: {tf15_details['Supertrend']}

🔔 Watch this strike!
"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=data)
    return response.status_code == 200
