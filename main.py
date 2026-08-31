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
CHAT_ID = "@Tamilstarforextradingboat"  # உங்கள் நேரடி சேனல் யூசர்நேம்

# 100% லைவ் டேட்டா கிடைக்கும் 10 OTC Pairs
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

# --- 2. FLASK SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "TamilStar VIP SMC Bot Running Live!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

# --- 3. TELEGRAM SENDER ---
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=6)
    except Exception as e:
        print(f"Send Error: {e}")

# --- 4. ACCURATE SMC INDICATORS ---
def calculate_indicators(df):
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['Body'] = (df['Close'] - df['Open']).abs()
    df['Range'] = df['High'] - df['Low']

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=10).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=10).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- 5. SURE-SHOT SCANNER ---
def check_asset(asset_name, ticker):
    global last_global_signal_time
    try:
        now_ts = time.time()
        # 2.5 நிமிட இடைவெளி (Spam தடுக்க)
        if (now_ts - last_global_signal_time) < 150:
            return

        df = yf.download(tickers=ticker, period="1d", interval="1m", progress=False, timeout=5)
        if df is None or df.empty or len(df) < 25:
            return

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        df = calculate_indicators(df)
        c1 = df.iloc[-2]  # சமீபத்திய முடிந்த 1-மினிட் கேண்டில்
        c2 = df.iloc[-3]

        if c1['Range'] == 0:
            return

        is_solid = (c1['Body'] / c1['Range']) >= 0.50

        # SMC + Momentum Entry
        call_sureshot = (
            (c1['Close'] > c1['Open']) and
            (c1['EMA_9'] >= c1['EMA_21']) and
            (52 <= c1['RSI'] <= 78) and
            is_solid
        )

        put_sureshot = (
            (c1['Close'] < c1['Open']) and
            (c1['EMA_9'] <= c1['EMA_21']) and
            (22 <= c1['RSI'] <= 48) and
            is_solid
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

# --- 6. CONTINUOUS RUNNER ---
def start_bot():
    print("TamilStar VIP SMC Bot Live...")
    time.sleep(2)
    # ஸ்டார்ட் ஆனதும் டெலிகிராமிற்கு நேரடி கன்பர்மேஷன்
    send_telegram(
        "╔═══════════════════╗\n"
        "   🚀 <b>TAMILSTAR BOT ACTIVE</b> 🚀\n"
        "╚═══════════════════╝\n\n"
        "<i>VIP SMC 1-Min Sure-Shot Scanner is Live!</i>"
    )
    while True:
        for name, ticker in OTC_PAIRS.items():
            check_asset(name, ticker)
            time.sleep(0.5)
        time.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    start_bot()
      
