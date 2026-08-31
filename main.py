import time
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import threading
from flask import Flask

# --- 1. QUOTEX / BINARY OTC BOT CONFIG ---
BOT_TOKEN = "8837639367:AAEQTwjnl9Ed9Pg9Ln3r6GS1WIjnSlClzG8"
CHAT_ID = "@Tamilstarforextradingboat"

# 13 QUOTEX OTC ASSETS
OTC_ASSETS = {
    "USD/INR (OTC)": "USDINR=X",
    "USD/BDT (OTC)": "USDBDT=X",
    "USD/PKR (OTC)": "USDPKR=X",
    "USD/BRL (OTC)": "USDBRL=X",
    "USD/MXN (OTC)": "USDMXN=X",
    "USD/COP (OTC)": "USDCOP=X",
    "USD/PHP (OTC)": "USDPHP=X",
    "USD/IDR (OTC)": "USDIDR=X",
    "USD/DZD (OTC)": "USDDZD=X",
    "USD/ARS (OTC)": "USDARS=X",
    "USD/ZAR (OTC)": "USDZAR=X",
    "USD/NGN (OTC)": "USDNGN=X",
    "USD/EGP (OTC)": "USDEGP=X"
}

TIMEFRAME = "1m"
last_signals = {}

# --- 2. FLASK SERVER (RENDER KEEP-ALIVE) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Quotex 13-OTC SureShot Bot Live!"

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
        requests.post(url, json=payload, timeout=8)
    except Exception as e:
        print(f"Telegram Error: {e}")

# --- 4. FAST SMC MOMENTUM INDICATORS ---
def calculate_indicators(df):
    df['SMA_5'] = df['Close'].rolling(window=5).mean()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['Body'] = (df['Close'] - df['Open']).abs()
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
        data = yf.download(tickers=ticker, period="1d", interval=TIMEFRAME, progress=False, timeout=6)
        if data is None or data.empty or len(data) < 20:
            return

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]

        df = calculate_indicators(data)
        c1 = df.iloc[-2]   # Last closed candle
        c2 = df.iloc[-3]
        c3 = df.iloc[-4]
        candle_time = df.index[-2]

        if last_signals.get(ticker) == candle_time:
            return

        # 1. 55%+ Solid Candle Body (No Doji)
        is_solid = (c1['Range'] > 0) and ((c1['Body'] / c1['Range']) >= 0.55)

        # 2. 3-Candle Trap Guard
        three_greens = (c1['Close'] > c1['Open']) and (c2['Close'] > c2['Open']) and (c3['Close'] > c3['Open'])
        three_reds   = (c1['Close'] < c1['Open']) and (c2['Close'] < c2['Open']) and (c3['Close'] < c3['Open'])

        # 3. Momentum Signals
        call_momentum = (c1['SMA_5'] >= c1['SMA_20']) and (c1['Close'] > c1['Open']) and (not three_greens) and (c1['RSI'] > 50 and c1['RSI'] < 80)
        put_momentum  = (c1['SMA_5'] <= c1['SMA_20']) and (c1['Close'] < c1['Open']) and (not three_reds) and (c1['RSI'] < 50 and c1['RSI'] > 20)

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
        pass

# --- 6. CONTINUOUS 24/7 SCANNER ---
def start_bot():
    print("Quotex OTC Bot Starting...")
    send_telegram("🚀 <b>TamilStar Quotex 13-OTC Bot Connected & Scanning Live!</b>")
    while True:
        for name, ticker in OTC_ASSETS.items():
            check_asset(name, ticker)
            time.sleep(0.4)
        time.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    start_bot()
      
