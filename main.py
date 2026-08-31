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

# 100% ரியல் லைவ் ஃபீட் உள்ள Quotex OTC அசெட்கள்
OTC_TICKERS = {
    "USD/INR (OTC)": "USDINR=X",
    "USD/BRL (OTC)": "USDBRL=X",
    "USD/MXN (OTC)": "USDMXN=X",
    "USD/COP (OTC)": "USDCOP=X",
    "USD/PHP (OTC)": "USDPHP=X",
    "USD/IDR (OTC)": "USDIDR=X",
    "USD/ZAR (OTC)": "USDZAR=X",
    "USD/EGP (OTC)": "USDEGP=X",
    "USD/BDT (OTC)": "USDBDT=X",
    "USD/PKR (OTC)": "USDPKR=X"
}

IST = pytz.timezone('Asia/Kolkata')
trade_active_until = 0
last_sent_minute = ""
discovered_chat_id = None

# --- 2. FLASK SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "TamilStar OTC 100% Real Trend Bot Live!"

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

# --- 4. HD IMAGE GENERATOR ---
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
    clean_asset = asset_name.replace(" (OTC)", "").replace("/", " ")

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

# --- 6. REAL LIVE CANDLE DATA ---
def fetch_real_candles(ticker):
    try:
        df = yf.download(tickers=ticker, period="1d", interval="1m", progress=False, timeout=4)
        if df is not None and not df.empty and len(df) >= 30:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]
            return df[['Open', 'High', 'Low', 'Close']].copy()
    except Exception:
        pass
    return None

# --- 7. INDICATORS & MARKET STRUCTURE ---
def calculate_indicators(df):
    df['EMA_9']  = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()

    df['Body']  = (df['Close'] - df['Open']).abs()
    df['Range'] = df['High'] - df['Low']

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- 8. SCANNER WITH STRICT TREND LOCK ---
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

        df = calculate_indicators(df)
        c1 = df.iloc[-1]  # கரண்ட் க்ளோசிங் கேண்டில்
        c2 = df.iloc[-2]
        c3 = df.iloc[-3]

        if c1['Range'] == 0:
            return

        is_solid = (c1['Body'] / c1['Range']) >= 0.60

        # Market Structure: Higher High & Higher Low
        is_higher_highs = (c1['High'] > c2['High']) and (c2['High'] > c3['High'])
        is_lower_lows   = (c1['Low'] < c2['Low']) and (c2['Low'] < c3['Low'])

        # Strict Trend Guard (EMA 9, 21, 50)
        is_uptrend   = (c1['EMA_9'] > c1['EMA_21']) and (c1['EMA_21'] > c1['EMA_50']) and (c1['Close'] > c1['EMA_9'])
        is_downtrend = (c1['EMA_9'] < c1['EMA_21']) and (c1['EMA_21'] < c1['EMA_50']) and (c1['Close'] < c1['EMA_9'])

        # 1. ஸ்ட்ராங் அப்-டிரெண்ட் / HH-ல் இருக்கும்போது கண்டிப்பா CALL மட்டுமே வரும்!
        call_sureshot = (
            is_uptrend and
            (is_higher_highs or c1['Close'] > c2['High']) and
            (c1['Close'] > c1['Open']) and
            (52 <= c1['RSI'] <= 78) and
            is_solid
        )

        # 2. ஸ்ட்ராங் டவுன்-டிரெண்ட் / LL-ல் இருக்கும்போது கண்டிப்பா PUT மட்டுமே வரும்!
        put_sureshot = (
            is_downtrend and
            (is_lower_lows or c1['Close'] < c2['Low']) and
            (c1['Close'] < c1['Open']) and
            (22 <= c1['RSI'] <= 48) and
            is_solid
        )

        signal = None
        if call_sureshot:
            signal = "CALL"
        elif put_sureshot:
            signal = "PUT"

        if signal:
            last_sent_minute = current_minute_str
            trade_active_until = now_ts + 180  # 3 நிமிடம் லாக்

            entry_time = (now_ist + timedelta(minutes=1)).strftime("%H:%M")
            photo_bytes = generate_signal_image(entry_time, asset_name, signal)
            caption = (
                f"👑 <b>TAMILSTAR OTC VIP SURE-SHOT</b> 👑\n\n"
                f"📊 <b>ASSET :</b> {asset_name}\n"
                f"⏰ <b>ENTRY TIME :</b> <b>{entry_time} (1-MIN)</b>\n"
                f"🎯 <b>DIRECTION :</b> {'🟢 CALL / BUY (UP)' if signal == 'CALL' else '🔴 PUT / SELL (DOWN)'}\n"
                f"⚡ <b>EXPIRY :</b> 1 MINUTE\n"
                f"🛡 <b>STRUCTURE :</b> {'HIGHER HIGH BULLISH' if signal == 'CALL' else 'LOWER LOW BEARISH'}\n\n"
                f"<i>(Use 1-Step MTG only if needed)</i>"
            )

            print(f"[{entry_time}] Signal Sent: {asset_name} -> {signal}")
            send_telegram_photo(photo_bytes, caption)

    except Exception:
        pass

# --- 9. SCANNER LOOP ---
def start_bot():
    print("TamilStar Live Market Scanner Active...")
    time.sleep(2)
    get_channel_id()
    while True:
        for name, ticker in OTC_TICKERS.items():
            check_asset(name, ticker)
            time.sleep(0.4)
        time.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    start_bot()
          
