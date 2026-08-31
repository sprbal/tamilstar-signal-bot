import time
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import threading
from flask import Flask

# --- 1. BOT & CHANNEL CONFIG ---
BOT_TOKEN = "8837639367:AAEQTwjnl9Ed9Pg9Ln3r6GS1WIjnSlClzG8"
CHAT_ID = "@Tamilstarforextradingboat"

OTC_ASSETS = {
    "EUR/USD (OTC)": "EURUSD=X",
    "GBP/USD (OTC)": "GBPUSD=X",
    "USD/JPY (OTC)": "USDJPY=X",
    "USD/INR (OTC)": "USDINR=X",
    "USD/BRL (OTC)": "USDBRL=X",
    "USD/MXN (OTC)": "USDMXN=X",
    "USD/CAD (OTC)": "USDCAD=X",
    "AUD/USD (OTC)": "AUDUSD=X",
    "USD/ZAR (OTC)": "USDZAR=X"
}

TIMEFRAME = "1m"
last_signals = {}

# --- 2. FLASK SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "PSB 1M OTC Bot Running Live!"

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
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

# --- 4. FAST MOMENTUM INDICATORS ---
def calculate_indicators(df):
    df['SMA_5']  = df['Close'].rolling(window=5).mean()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    
    df['Body']  = (df['Close'] - df['Open']).abs()
    df['Range'] = df['High'] - df['Low']

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    return df

# --- 5. SIGNAL SCANNER ---
def check_asset(asset_name, ticker):
    global last_signals
    try:
        data = yf.download(tickers=ticker, period="1d", interval=TIMEFRAME, progress=False)
        if data is None or data.empty or len(data) < 25:
            return

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]

        df = calculate_indicators(data)
        
        c1 = df.iloc[-2]   # Last closed candle
        candle_time = df.index[-2]

        if last_signals.get(ticker) == candle_time:
            return

        # 60%+ Body Filter (Doji Skip)
        is_solid = (c1['Range'] > 0) and ((c1['Body'] / c1['Range']) >= 0.60)

        # Trend & Momentum Logic
        call_momentum = (c1['SMA_5'] >= c1['SMA_20']) and (c1['Close'] > c1['Open']) and (c1['RSI'] > 52)
        put_momentum  = (c1['SMA_5'] <= c1['SMA_20']) and (c1['Close'] < c1['Open']) and (c1['RSI'] < 48)

        signal = None

        if call_momentum and is_solid:
            signal = "CALL"
        elif put_momentum and is_solid:
            signal = "PUT"

        if signal:
            last_signals[ticker] = candle_time
            entry_time = (datetime.now() + timedelta(minutes=1)).strftime("%H:%M")

            if signal == "CALL":
                msg = (
                    f"🟢 <b>ASSET : {asset_name}</b>\n"
                    f"⏰ <b>TIME : {entry_time} (1-MIN)</b>\n\n"
                    f"🟢🟢 <b>CALL / BUY (UP)</b> 🟢🟢\n"
                    f"⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️\n"
                    f"⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️\n"
                    f"⬆️⬆️ <b>ENTER UP</b> ⬆️⬆️\n"
                    f"⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️\n"
                    f"⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️"
                )
            else:
                msg = (
                    f"🔴 <b>ASSET : {asset_name}</b>\n"
                    f"⏰ <b>TIME : {entry_time} (1-MIN)</b>\n\n"
                    f"🔴🔴 <b>PUT / SELL (DOWN)</b> 🔴🔴\n"
                    f"⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️\n"
                    f"⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️\n"
                    f"⬇️⬇️ <b>ENTER DOWN</b> ⬇️⬇️\n"
                    f"⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️\n"
                    f"⬇️⬇️⬇️⬇️⬇️⬇️⬇️⬇️"
                )

            print(f"[{datetime.now()}] Signal Sent: {asset_name} -> {signal} at {entry_time}")
            send_telegram(msg)

    except Exception as e:
        print(f"Scan Error {asset_name}: {e}")

# --- 6. CONTINUOUS RUNNER ---
def start_bot():
    print("Bot Starting...")
    send_telegram("🚀 <b>PSB OTC Bot Connected & Scanning Live!</b>\n<i>Signals will appear here automatically.</i>")
    
    while True:
        for name, ticker in OTC_ASSETS.items():
            check_asset(name, ticker)
            time.sleep(1)
        time.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    start_bot()
          
