import time
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import threading
from flask import Flask

# --- 1. BOT & CHANNEL CONFIG ---
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"          # உங்க பைனரி Telegram Bot Token
CHAT_ID = "@Tamilstarforextradingboat"      # உங்க Telegram Channel ID

# 13 OTC அசெட்கள்
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

# --- 2. FLASK SERVER (Render 24/7 Hosting) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "PSB 13-OTC Pure SureShot Bot is Running Live!"

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

# --- 4. INDICATOR ENGINE (SMC, SMA & MOMENTUM) ---
def calculate_indicators(df):
    df['SMA_5']  = df['Close'].rolling(window=5).mean()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()

    # Candle Body vs Wick
    df['Body']  = (df['Close'] - df['Open']).abs()
    df['Range'] = df['High'] - df['Low']
    df['ATR']   = df['Range'].rolling(window=10).mean()

    # Fast RSI (7)
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
        data = yf.download(tickers=ticker, period="1d", interval=TIMEFRAME, progress=False)
        if data.empty or len(data) < 60:
            return

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]

        df = calculate_indicators(data)
        
        c1 = df.iloc[-2]   # Last closed candle
        c2 = df.iloc[-3]   # Previous candle
        c3 = df.iloc[-4]   # 3rd candle
        candle_time = df.index[-2]

        if last_signals.get(ticker) == candle_time:
            return

        # 1. 75%+ Solid Big Candle Body (Doji / Small Wick Block)
        is_big_candle = (c1['Range'] > 0) and ((c1['Body'] / c1['Range']) >= 0.75) and (c1['Body'] >= c1['ATR'] * 1.1)

        # 2. 3-Candle Trap Lock (தொடர்ந்து 3 கேண்டில் போயிட்டா என்ட்ரி வராது)
        three_greens = (c1['Close'] > c1['Open']) and (c2['Close'] > c2['Open']) and (c3['Close'] > c3['Open'])
        three_reds   = (c1['Close'] < c1['Open']) and (c2['Close'] < c2['Open']) and (c3['Close'] < c3['Open'])

        # 3. Pure Trend Alignment
        is_uptrend   = (c1['SMA_5'] > c1['SMA_20']) and (c1['Close'] > c1['EMA_50'])
        is_downtrend = (c1['SMA_5'] < c1['SMA_20']) and (c1['Close'] < c1['EMA_50'])

        # 4. Round Level Momentum
        price_str = f"{c1['Close']:.4f}"
        last_digits = int(price_str.split('.')[-1][-2:]) if '.' in price_str else 0
        is_level_break_call = last_digits > 10 and last_digits < 90
        is_level_break_put  = last_digits < 90 and last_digits > 10

        signal = None

        # CALL LOGIC
        if is_uptrend and is_big_candle and (c1['Close'] > c1['Open']) and (not three_greens) and is_level_break_call and (c1['RSI'] > 58 and c1['RSI'] < 75):
            signal = "CALL"

        # PUT LOGIC
        elif is_downtrend and is_big_candle and (c1['Close'] < c1['Open']) and (not three_reds) and is_level_break_put and (c1['RSI'] < 42 and c1['RSI'] > 25):
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

            print(f"[{datetime.now()}] Live Signal: {asset_name} -> {signal} at {entry_time}")
            send_telegram(msg)

    except Exception as e:
        print(f"Error scanning {asset_name}: {e}")

# --- 6. 24/7 ULTRA FAST SCANNER LOOP ---
def start_bot():
    print("PSB Ultra Clean OTC Scanner Started Live...")
    while True:
        for name, ticker in OTC_ASSETS.items():
            check_asset(name, ticker)
            time.sleep(0.4)
        time.sleep(3)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    start_bot()
          
