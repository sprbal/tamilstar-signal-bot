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

# 100% ரியல் லைவ் டேட்டா வரும் OTC & Major Pairs
OTC_PAIRS = {
    "USD/INR (OTC)": "USDINR=X",
    "USD/BRL (OTC)": "USDBRL=X",
    "USD/MXN (OTC)": "USDMXN=X",
    "USD/COP (OTC)": "USDCOP=X",
    "USD/PHP (OTC)": "USDPHP=X",
    "USD/IDR (OTC)": "USDIDR=X",
    "USD/ZAR (OTC)": "USDZAR=X",
    "USD/EGP (OTC)": "USDEGP=X",
    "EUR/USD (OTC)": "EURUSD=X",
    "GBP/USD (OTC)": "GBPUSD=X"
}

IST = pytz.timezone('Asia/Kolkata')
last_global_signal_time = 0
discovered_chat_id = None

# --- 2. FLASK SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "TamilStar VIP SMC OTC Bot Running Live!"

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

# --- 5. HIGH ACCURACY SMC & PRICE ACTION STRATEGY ---
def calculate_indicators(df):
    # Trend Filter
    df['EMA_9']  = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()

    # Candle Dimensions
    df['Body']  = (df['Close'] - df['Open']).abs()
    df['Range'] = df['High'] - df['Low']
    df['Upper_Wick'] = df['High'] - df[['Close', 'Open']].max(axis=1)
    df['Lower_Wick'] = df[['Close', 'Open']].min(axis=1) - df['Low']

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    return df

# --- 6. SURE-SHOT SIGNAL SCANNER ---
def check_asset(asset_name, ticker):
    global last_global_signal_time
    try:
        now_ts = time.time()
        # 4 நிமிட கூல்டவுன் (அவசரப்பட்டு சிக்னல் கொடுக்காமல் பெஸ்ட் சிக்னல் மட்டும் கொடுக்கும்)
        if (now_ts - last_global_signal_time) < 240:
            return

        df = yf.download(tickers=ticker, period="1d", interval="1m", progress=False, timeout=5)
        if df is None or df.empty or len(df) < 55:
            return

        if isinstance(df.columns, pd.MultiIndex):
            data_cols = [col[0] for col in df.columns]
            df.columns = data_cols

        df = calculate_indicators(df)
        
        c1 = df.iloc[-2]  # Last closed 1-min candle
        c2 = df.iloc[-3]  # Previous candle

        # 1. Solid Candle Body & Rejection Filter
        if c1['Range'] == 0:
            return
        body_ratio = c1['Body'] / c1['Range']
        
        # 2. SMC Bullish Sure-Shot Rule:
        # - Strong Bullish Candle (Body > 60%)
        # - Lower Wick Rejection (buyers pushing price up)
        # - EMA 9 > EMA 21 > EMA 50 (Strong Up-Trend)
        # - RSI between 54 and 72 (Healthy Momentum, Not Overbought)
        call_sureshot = (
            (c1['Close'] > c1['Open']) and
            (body_ratio >= 0.60) and
            (c1['Lower_Wick'] > c1['Upper_Wick']) and
            (c1['EMA_9'] > c1['EMA_21']) and (c1['EMA_21'] > c1['EMA_50']) and
            (54 <= c1['RSI'] <= 72) and
            (c1['Close'] > c2['High'])
        )

        # 3. SMC Bearish Sure-Shot Rule:
        # - Strong Bearish Candle (Body > 60%)
        # - Upper Wick Rejection (sellers pushing price down)
        # - EMA 9 < EMA 21 < EMA 50 (Strong Down-Trend)
        # - RSI between 28 and 46 (Healthy Momentum, Not Oversold)
        put_sureshot = (
            (c1['Close'] < c1['Open']) and
            (body_ratio >= 0.60) and
            (c1['Upper_Wick'] > c1['Lower_Wick']) and
            (c1['EMA_9'] < c1['EMA_21']) and (c1['EMA_21'] < c1['EMA_50']) and
            (28 <= c1['RSI'] <= 46) and
            (c1['Close'] < c2['Low'])
        )

        signal = None
        if call_sureshot:
            signal = "CALL"
        elif put_sureshot:
            signal = "PUT"

        if signal:
            last_global_signal_time = now_ts
            now_ist = datetime.now(IST)
            entry_time = (now_ist + timedelta(minutes=1)).strftime("%H:%M")

            if signal == "CALL":
                msg = (
                    f"╔═══════════════════╗\n"
                    f"   👑 <b>TAMILSTAR VIP OTC</b> 👑\n"
                    f"╚═══════════════════╝\n\n"
                    f"📊 <b>ASSET</b>      : <code>{asset_name}</code>\n"
                    f"⏰ <b>ENTRY TIME</b> : <b>{entry_time} (1-MIN)</b>\n"
                    f"🎯 <b>DIRECTION</b>  : 🟢 <b>CALL / BUY</b> 🟢\n"
                    f"⚡ <b>EXPIRY</b>     : <b>1 MINUTE</b>\n"
                    f"🛡 <b>STRATEGY</b>   : <b>SMC SURE-SHOT</b>\n\n"
                    f"          ⬆️\n"
                    f"          ⬆️\n\n"
                    f"<i>Use 1-Step MTG only if needed.</i>"
                )
            else:
                msg = (
                    f"╔═══════════════════╗\n"
                    f"   👑 <b>TAMILSTAR VIP OTC</b> 👑\n"
                    f"╚═══════════════════╝\n\n"
                    f"📊 <b>ASSET</b>      : <code>{asset_name}</code>\n"
                    f"⏰ <b>ENTRY TIME</b> : <b>{entry_time} (1-MIN)</b>\n"
                    f"🎯 <b>DIRECTION</b>  : 🔴 <b>PUT / SELL</b> 🔴\n"
                    f"⚡ <b>EXPIRY</b>     : <b>1 MINUTE</b>\n"
                    f"🛡 <b>STRATEGY</b>   : <b>SMC SURE-SHOT</b>\n\n"
                    f"          ⬇️\n"
                    f"          ⬇️\n\n"
                    f"<i>Use 1-Step MTG only if needed.</i>"
                )

            print(f"[{entry_time}] Sure-Shot Sent: {asset_name} -> {signal}")
            send_telegram(msg)

    except Exception:
        pass

# --- 7. CONTINUOUS RUNNER ---
def start_bot():
    print("TamilStar VIP SMC Bot Running...")
    time.sleep(2)
    get_channel_id()
    while True:
        for name, ticker in OTC_PAIRS.items():
            check_asset(name, ticker)
            time.sleep(0.5)
        time.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    start_bot()
  
