import time
import io
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import threading
from flask import Flask
from PIL import Image, ImageDraw, ImageFont

# --- 1. BOT CONFIG ---
BOT_TOKEN = "8837639367:AAEQTwjnl9Ed9Pg9Ln3r6GS1WIjnSlClzG8"

# 100% ரியல் லைவ் மார்க்கெட் ஃபாரெக்ஸ் ஜோடிகள்
FOREX_PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "USD/CHF": "USDCHF=X"
}

IST = pytz.timezone('Asia/Kolkata')
trade_active_until = 0
last_sent_minute = ""
discovered_chat_id = None

# --- 2. FLASK SERVER (Render Keep-Alive) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "TamilStar Real Market Master Price Action Bot Live!"

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

# --- 4. HD IMAGE CARD GENERATOR ---
def generate_signal_image(time_str, asset_name, signal_type):
    width, height = 750, 900
    img = Image.new("RGB", (width, height), color="#FFFFFF")
    draw = ImageDraw.Draw(img)

    try:
        font_time = ImageFont.truetype("DejaVuSans-Bold.ttf", 68)
        font_asset = ImageFont.truetype("DejaVuSans-Bold.ttf", 56)
        font_dir = ImageFont.truetype("DejaVuSans-Bold.ttf", 46)
    except Exception:
        font_time = font_asset = font_dir = ImageFont.load_default()

    is_call = (signal_type == "CALL")
    theme_color = "#00C853" if is_call else "#D50000"
    clean_asset = asset_name.replace("/", " ")

    draw.text((width / 2, 80), time_str, fill=theme_color, font=font_time, anchor="mm")
    draw.text((width / 2, 160), clean_asset, fill=theme_color, font=font_asset, anchor="mm")

    if is_call:
        arrow_points = [
            (375, 250), (560, 440), (460, 440),
            (460, 680), (290, 680), (290, 440), (190, 440)
        ]
        direction_text = "CALL / BUY (UP)"
    else:
        arrow_points = [
            (290, 250), (460, 250), (460, 490),
            (560, 490), (375, 680), (190, 490), (290, 490)
        ]
        direction_text = "PUT / SELL (DOWN)"

    draw.polygon(arrow_points, fill=theme_color)
    draw.text((width / 2, 780), direction_text, fill=theme_color, font=font_dir, anchor="mm")

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

# --- 5. TELEGRAM SENDER ---
def send_telegram_photo(photo_bytes, caption):
    global discovered_chat_id
    cid = discovered_chat_id or get_channel_id()
    if not cid:
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    files = {"photo": ("signal.png", photo_bytes, "image/png")}
    data = {"chat_id": cid, "caption": caption, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data, files=files, timeout=10)
    except Exception:
        pass

# --- 6. REAL LIVE 1-MIN CANDLE FETCHER ---
def fetch_real_candles(ticker):
    try:
        df = yf.download(tickers=ticker, period="1d", interval="1m", progress=False, timeout=5)
        if df is not None and not df.empty and len(df) >= 30:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]
            return df[['Open', 'High', 'Low', 'Close']].copy()
    except Exception:
        pass
    return None

# --- 7. ADVANCED PRICE ACTION & FIBONACCI SCANNER ---
def analyze_market(df):
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()

    # Candles
    c1 = df.iloc[-1]  # சமீபத்தில் முடிந்த கேண்டில்
    c2 = df.iloc[-2]
    c3 = df.iloc[-3]
    c4 = df.iloc[-4]
    c5 = df.iloc[-5]

    colors = ["G" if row['Close'] >= row['Open'] else "R" for _, row in df.tail(10).iterrows()]
    cl1, cl2, cl3, cl4, cl5 = colors[-1], colors[-2], colors[-3], colors[-4], colors[-5]

    # Structure & Trend
    is_uptrend = (c1['EMA_9'] > c1['EMA_21']) and (c1['EMA_21'] > c1['EMA_50'])
    is_downtrend = (c1['EMA_9'] < c1['EMA_21']) and (c1['EMA_21'] < c1['EMA_50'])

    # Swing High & Low for Fibonacci 0.50 - 0.618
    recent_high = df['High'].tail(25).max()
    recent_low = df['Low'].tail(25).min()
    fib_diff = recent_high - recent_low

    fib_50 = recent_high - 0.50 * fib_diff
    fib_618 = recent_high - 0.618 * fib_diff

    # SNR Key Levels (2nd/3rd Touch Detection)
    snr_resistance = df['High'].tail(20).nlargest(3).mean()
    snr_support = df['Low'].tail(20).nsmallest(3).mean()

    signal = None
    strategy_name = ""

    # 1. 4TH CANDLE ALTERNATION STRATEGY
    if (cl5 == "G" and cl4 == "G") and (cl3 == "R" and cl2 == "G" and cl1 == "R"):
        signal = "CALL"
        strategy_name = "4th Candle Alternation Wave (CALL)"
    elif (cl5 == "R" and cl4 == "R") and (cl3 == "G" and cl2 == "R" and cl1 == "G"):
        signal = "PUT"
        strategy_name = "4th Candle Alternation Wave (PUT)"

    # 2. FIBONACCI 0.50 - 0.618 GOLDEN RETRACEMENT REVERSAL
    elif is_uptrend and (fib_618 <= c1['Low'] <= fib_50) and (c1['Close'] > c1['Open']):
        signal = "CALL"
        strategy_name = "Fibonacci 0.50-0.618 Golden Bounce"
    elif is_downtrend and (fib_50 <= c1['High'] <= fib_618) and (c1['Close'] < c1['Open']):
        signal = "PUT"
        strategy_name = "Fibonacci 0.50-0.618 Golden Rejection"

    # 3. STRONG SNR 2ND/3RD TOUCH WICK REVERSAL
    elif abs(c1['Low'] - snr_support) < 0.0003 and (c1['Close'] > c1['Open']) and ((c1['Close'] - c1['Low']) > (c1['High'] - c1['Close'])):
        signal = "CALL"
        strategy_name = "Strong Support Touch & Lower Wick Reversal"
    elif abs(c1['High'] - snr_resistance) < 0.0003 and (c1['Close'] < c1['Open']) and ((c1['High'] - c1['Close']) > (c1['Close'] - c1['Low'])):
        signal = "PUT"
        strategy_name = "Strong Resistance Touch & Upper Wick Reversal"

    # 4. GAP FILLING TO NEXT SNR LEVEL
    elif is_uptrend and (snr_resistance - c1['Close'] > 0.0006) and (c1['Close'] > c2['High']):
        signal = "CALL"
        strategy_name = "Gap Filling to Resistance Target"
    elif is_downtrend and (c1['Close'] - snr_support > 0.0006) and (c1['Close'] < c2['Low']):
        signal = "PUT"
        strategy_name = "Gap Filling to Support Target"

    # 5. BREAKOUT & RETEST CONTINUATION (BOS)
    elif is_uptrend and (c2['Close'] > snr_resistance) and (c1['Low'] <= snr_resistance) and (c1['Close'] > snr_resistance):
        signal = "CALL"
        strategy_name = "Breakout Retest Continuation (BOS)"
    elif is_downtrend and (c2['Close'] < snr_support) and (c1['High'] >= snr_support) and (c1['Close'] < snr_support):
        signal = "PUT"
        strategy_name = "Breakdown Retest Continuation (BOS)"

    return signal, strategy_name

# --- 8. SCANNER ENGINE ---
def check_asset(asset_name, ticker):
    global trade_active_until, last_sent_minute
    try:
        now_ts = time.time()
        if now_ts < trade_active_until:
            return

        now_ist = datetime.now(IST)
        current_minute_str = now_ist.strftime("%Y-%m-%d %H:%M")
        if current_minute_str == last_sent_minute:
            return

        df = fetch_real_candles(ticker)
        if df is None or len(df) < 30:
            return

        signal, strategy_name = analyze_market(df)

        if signal:
            last_sent_minute = current_minute_str
            trade_active_until = now_ts + 180  # 3 நிமிடம் கூல்டவுன் லாக்

            entry_time = (now_ist + timedelta(minutes=1)).strftime("%H:%M")
            photo_bytes = generate_signal_image(entry_time, asset_name, signal)
            caption = (
                f"👑 <b>TAMILSTAR REAL MARKET VIP</b> 👑\n\n"
                f"📊 <b>ASSET :</b> {asset_name}\n"
                f"⏰ <b>ENTRY TIME :</b> <b>{entry_time} (1-MIN)</b>\n"
                f"🎯 <b>DIRECTION :</b> {'🟢 CALL / BUY (UP)' if signal == 'CALL' else '🔴 PUT / SELL (DOWN)'}\n"
                f"⚡ <b>EXPIRY :</b> 1 MINUTE\n"
                f"🛡 <b>CONFLUENCE :</b> {strategy_name}\n\n"
                f"<i>(Use 1-Step MTG only if needed)</i>"
            )

            print(f"[{entry_time}] Real Signal Sent: {asset_name} -> {signal} ({strategy_name})")
            send_telegram_photo(photo_bytes, caption)

    except Exception:
        pass

# --- 9. SCANNER LOOP ---
def start_bot():
    print("TamilStar Real Forex Price Action Engine Live...")
    time.sleep(2)
    get_channel_id()
    while True:
        for name, ticker in FOREX_PAIRS.items():
            check_asset(name, ticker)
            time.sleep(0.4)
        time.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    start_bot()
              
