import time
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import threading
from flask import Flask

# --- 1. BOT CONFIG ---
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"          # உங்க Telegram Bot Token
CHAT_ID = "@Tamilstarforextradingboat"      # உங்க Telegram Channel ID

# yfinance-ல் 1-Minute டேட்டா பக்காவா கிடைக்கக்கூடிய OTC/Forex ஜோடிகள்
OTC_ASSETS = {
    "USD/INR (OTC)": "USDINR=X",
    "USD/BRL (OTC)": "USDBRL=X",
    "USD/MXN (OTC)": "USDMXN=X",
    "USD/COP (OTC)": "USDCOP=X",
    "USD/PHP (OTC)": "USDPHP=X",
    "USD/IDR (OTC)": "USDIDR=X",
    "USD/ZAR (OTC)": "USDZAR=X",
    "USD/EGP (OTC)": "USDEGP=X",
    "EUR/USD (OTC)": "EURUSD=X",
    "GBP/USD (OTC)": "GBPUSD=X",
    "USD/JPY (OTC)": "USDJPY=X",
    "AUD/USD (OTC)": "AUDUSD=X",
    "USD/CAD (OTC)": "USDCAD=X"
}

TIMEFRAME = "1m"
last_signals = {}

# --- 2. FLASK SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "PSB 13-OTC Ultra Fast Bot Live!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

# --- 3. TELEGRAM DISPATCHER ---
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

# --- 4. INDICATOR ENGINE ---
def calculate_indicators(df):
    df['SMA_5']  = df['Close'].rolling(window=5).mean()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()

    df['Body']  = (df['Close'] - df['Open']).abs()
    df['Range'] = df['High'] - df['Low']
    df['ATR']   = df['Range'].rolling(window=10).mean()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    return df

# --- 5. ULTRA SURE-SHOT SCANNER ---
def check_asset(asset_name, ticker):
    global last_signals
    try:
        # Fetch 1-min data with 1-day range
        data = yf.download(tickers=ticker, period="1d", interval=TIMEFRAME, progress=False)
        if data is None or data.empty or len(data) < 30:
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

        # 1. 65%+ Solid Candle Body Filter (Doji Skip)
        is_solid = (c1['Range'] > 0) and ((c1['Body'] / c1['Range']) >= 0.65)

        # 2. 3-Candle Trap Guard
        three_greens = (c1['Close'] > c1['Open']) and (c2['Close'] > c2['Open']) and (c3['Close'] > c3['Open'])
        three_reds   = (c1['Close'] < c1['Open']) and (c2['Close'] < c2['Open']) and (c3['Close'] < c3['Open'])

        # 3. Pure Trend Direction
        is_uptrend   = (c1['SMA_5'] > c1['SMA_20']) and (c1['Close'] > c1['EMA_50'])
        is_downtrend = (c1['SMA_5'] < c1['SMA_20']) and (c1['Close'] < c1['EMA_50'])

        signal = None

        # CALL SURE-SHOT
        if is_uptrend and is_solid and (c1['Close'] > c1['Open']) and (not three_greens) and (c1['RSI'] > 55 and c1['RSI'] < 78):
            signal = "CALL"

        # PUT SURE-SHOT
        elif is_downtrend and is_solid and (c1['Close'] < c1['Open']) and (not three_reds) and (c1['RSI'] < 45 and c1['RSI'] > 22):
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
        print(f"Error checking {asset_name}: {e}")

# --- 6. 24/7 SCANNER LOOP ---
def start_bot():
    print("PSB Ultra Clean OTC Scanner Started Live...")
    while True:
        for name, ticker in OTC_ASSETS.items():
            check_asset(name, ticker)
            time.sleep(0.3)
        time.sleep(3)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    start_bot()
          
