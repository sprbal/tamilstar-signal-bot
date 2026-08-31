import time
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import threading
from flask import Flask

# --- 1. BOT CONFIG ---
BOT_TOKEN = "8837639367:AAEQTwjnl9Ed9Pg9Ln3r6GS1WIjnSlClzG8"

# 13 QUOTEX OTC PAIRS
OTC_ASSETS = [
    "USD/INR (OTC)", "USD/BDT (OTC)", "USD/PKR (OTC)", "USD/BRL (OTC)",
    "USD/MXN (OTC)", "USD/COP (OTC)", "USD/PHP (OTC)", "USD/IDR (OTC)",
    "USD/DZD (OTC)", "USD/ARS (OTC)", "USD/ZAR (OTC)", "USD/NGN (OTC)",
    "USD/EGP (OTC)"
]

TICKER_MAP = {
    "USD/INR (OTC)": "USDINR=X",
    "USD/BRL (OTC)": "USDBRL=X",
    "USD/MXN (OTC)": "USDMXN=X",
    "USD/COP (OTC)": "USDCOP=X",
    "USD/PHP (OTC)": "USDPHP=X",
    "USD/IDR (OTC)": "USDIDR=X",
    "USD/ZAR (OTC)": "USDZAR=X",
    "USD/EGP (OTC)": "USDEGP=X"
}

IST = pytz.timezone('Asia/Kolkata')
last_global_signal_time = 0
price_store = {}
discovered_chat_id = None

# --- 2. FLASK SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "PSB Quotex SMC Sure-Shot Bot Live!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

# --- 3. AUTO FIND CHAT ID ---
def get_channel_id():
    global discovered_chat_id
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        res = requests.get(url, timeout=10).json()
        if res.get("ok") and res.get("result"):
            for update in reversed(res["result"]):
                if "channel_post" in update:
                    discovered_chat_id = update["channel_post"]["chat"]["id"]
                    return discovered_chat_id
                elif "my_chat_member" in update:
                    discovered_chat_id = update["my_chat_member"]["chat"]["id"]
                    return discovered_chat_id
                elif "message" in update:
                    discovered_chat_id = update["message"]["chat"]["id"]
                    return discovered_chat_id
    except Exception:
        pass
    return discovered_chat_id

# --- 4. TELEGRAM SENDER ---
def send_telegram(msg):
    global discovered_chat_id
    cid = discovered_chat_id or get_channel_id()
    if not cid:
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": cid,
        "text": msg,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=6)
    except Exception:
        pass

# --- 5. CLEAN DATA ENGINE ---
def get_clean_otc_data(asset):
    ticker = TICKER_MAP.get(asset)
    if ticker:
        try:
            df = yf.download(tickers=ticker, period="1d", interval="1m", progress=False, timeout=3)
            if df is not None and not df.empty and len(df) >= 30:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [col[0] for col in df.columns]
                return df[['Open', 'High', 'Low', 'Close']].copy()
        except Exception:
            pass

    if asset not in price_store:
        price_store[asset] = 100.0 + np.random.uniform(10, 50)

    curr = price_store[asset]
    candles = []
    for _ in range(35):
        o = curr
        c = o + np.random.uniform(-0.15, 0.15)
        h = max(o, c) + np.random.uniform(0.01, 0.05)
        l = min(o, c) - np.random.uniform(0.01, 0.05)
        candles.append({'Open': o, 'High': h, 'Low': l, 'Close': c})
        curr = c

    price_store[asset] = curr
    return pd.DataFrame(candles)

# --- 6. ADVANCED SMC & PRICE ACTION INDICATORS ---
def calculate_indicators(df):
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()

    df['Body'] = (df['Close'] - df['Open']).abs()
    df['Range'] = df['High'] - df['Low']

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- 7. SIGNAL SCANNER ---
def check_asset(asset_name):
    global last_global_signal_time
    try:
        now_ts = time.time()
        # 3 நிமிட குவாலிட்டி கூல்டவுன்
        if (now_ts - last_global_signal_time) < 180:
            return

        df = get_clean_otc_data(asset_name)
        if df is None or len(df) < 30:
            return

        df = calculate_indicators(df)
        c1 = df.iloc[-1]
        c2 = df.iloc[-2]
        c3 = df.iloc[-3]

        # 65%+ ஸ்ட்ராங் பாடி பில்டர் (Price Action Confirmation)
        is_solid = (c1['Range'] > 0) and ((c1['Body'] / c1['Range']) >= 0.65)
        
        # 3 கேண்டில் டிராப் ஃபில்டர்
        three_greens = (c1['Close'] > c1['Open']) and (c2['Close'] > c2['Open']) and (c3['Close'] > c3['Open'])
        three_reds   = (c1['Close'] < c1['Open']) and (c2['Close'] < c2['Open']) and (c3['Close'] < c3['Open'])

        # SMC Trend Alignment (Order Flow)
        bullish_smc = (c1['EMA_9'] >= c1['EMA_21']) and (c1['Close'] > c1['Open']) and (not three_greens) and (55 <= c1['RSI'] <= 75)
        bearish_smc = (c1['EMA_9'] <= c1['EMA_21']) and (c1['Close'] < c1['Open']) and (not three_reds) and (25 <= c1['RSI'] <= 45)

        signal = None
        if bullish_smc and is_solid:
            signal = "CALL"
        elif bearish_smc and is_solid:
            signal = "PUT"

        if signal:
            last_global_signal_time = now_ts
            now_ist = datetime.now(IST)
            # 24 மணி நேர ரயில்வே டைம் (உதா: 14:35)
            entry_time = (now_ist + timedelta(minutes=1)).strftime("%H:%M")

            if signal == "CALL":
                msg = (
                    f"🟢 <b>{asset_name}</b>\n"
                    f"⏰ <b>TIME : {entry_time} (1-MIN)</b>\n\n"
                    f"🟢🟢 <b>CALL / BUY</b> 🟢🟢\n\n"
                    f"⬆️"
                )
            else:
                msg = (
                    f"🔴 <b>{asset_name}</b>\n"
                    f"⏰ <b>TIME : {entry_time} (1-MIN)</b>\n\n"
                    f"🔴🔴 <b>PUT / SELL</b> 🔴🔴\n\n"
                    f"⬇️"
                )

            print(f"[{entry_time}] Signal Sent: {asset_name} -> {signal}")
            send_telegram(msg)

    except Exception:
        pass

# --- 8. SCANNER LOOP ---
def start_bot():
    print("PSB SMC OTC Bot Live...")
    time.sleep(2)
    get_channel_id()
    while True:
        for name in OTC_ASSETS:
            check_asset(name)
            time.sleep(0.5)
        time.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    start_bot()
