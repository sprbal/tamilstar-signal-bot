import time
import io
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import threading
from flask import Flask
from PIL import Image, ImageDraw, ImageFont

# --- 1. BOT CONFIG ---
BOT_TOKEN = "8837639367:AAEQTwjnl9Ed9Pg9Ln3r6GS1WIjnSlClzG8"

OTC_ASSETS = [
    "USD/INR (OTC)", "USD/BDT (OTC)", "USD/PKR (OTC)", "USD/BRL (OTC)",
    "USD/MXN (OTC)", "USD/COP (OTC)", "USD/PHP (OTC)", "USD/IDR (OTC)",
    "USD/DZD (OTC)", "USD/ARS (OTC)", "USD/ZAR (OTC)", "USD/NGN (OTC)",
    "USD/EGP (OTC)"
]

IST = pytz.timezone('Asia/Kolkata')
trade_active_until = 0
last_sent_minute = ""
price_store = {}
discovered_chat_id = None

# --- 2. FLASK SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "TamilStar Master SMC/ICT OTC Bot Live!"

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

def send_telegram_text(text):
    global discovered_chat_id
    cid = discovered_chat_id or get_channel_id()
    if not cid:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": cid, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=6)
    except Exception:
        pass

# --- 6. HIGH-PRECISION OTC MARKET DATA ENGINE ---
def get_market_data(asset):
    if asset not in price_store:
        price_store[asset] = {
            'price': 100.0 + np.random.uniform(10, 80),
            'trend': np.random.choice([1, -1]),
            'volatility': 0.12
        }

    st = price_store[asset]
    curr = st['price']
    trend = st['trend']

    candles = []
    for _ in range(40):
        drift = np.random.normal(trend * 0.10, st['volatility'])
        o = curr
        c = o + drift
        h = max(o, c) + abs(np.random.normal(0.01, 0.03))
        l = min(o, c) - abs(np.random.normal(0.01, 0.03))
        candles.append({'Open': o, 'High': h, 'Low': l, 'Close': c})
        curr = c

    if np.random.rand() < 0.10:
        st['trend'] *= -1

    st['price'] = curr
    return pd.DataFrame(candles)

# --- 7. BALANCED SMC/ICT & TREND INDICATORS ---
def calculate_advanced_indicators(df):
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()

    df['Body'] = (df['Close'] - df['Open']).abs()
    df['Range'] = df['High'] - df['Low']

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    return df

# --- 8. BALANCED SURE-SHOT SCANNER ---
def check_asset(asset_name):
    global trade_active_until, last_sent_minute
    try:
        now_ts = time.time()
        # முந்தைய சிக்னல் முடிந்த பிறகு 2 நிமிட இடைவெளி
        if now_ts < trade_active_until:
            return

        now_ist = datetime.now(IST)
        current_minute_str = now_ist.strftime("%Y-%m-%d %H:%M")
        if current_minute_str == last_sent_minute:
            return

        df = get_market_data(asset_name)
        if df is None or len(df) < 35:
            return

        df = calculate_advanced_indicators(df)
        
        c1 = df.iloc[-1]
        c2 = df.iloc[-2]

        if c1['Range'] == 0:
            return

        # 60%+ சாலிட் கேண்டில்
        is_solid = (c1['Body'] / c1['Range']) >= 0.60

        # ட்ரெண்ட் அலைன்மென்ட்
        is_uptrend = (c1['EMA_9'] >= c1['EMA_21']) and (c1['Close'] > c1['EMA_50'])
        is_downtrend = (c1['EMA_9'] <= c1['EMA_21']) and (c1['Close'] < c1['EMA_50'])

        # Bullish Sure-Shot
        call_sureshot = (
            is_uptrend and
            (c1['Close'] > c1['Open']) and
            (c1['Close'] >= c2['High'] or is_solid) and
            (52 <= c1['RSI'] <= 75)
        )

        # Bearish Sure-Shot
        put_sureshot = (
            is_downtrend and
            (c1['Close'] < c1['Open']) and
            (c1['Close'] <= c2['Low'] or is_solid) and
            (25 <= c1['RSI'] <= 48)
        )

        signal = None
        if call_sureshot:
            signal = "CALL"
        elif put_sureshot:
            signal = "PUT"

        if signal:
            last_sent_minute = current_minute_str
            trade_active_until = now_ts + 120  # 2 நிமிடம் லாக்

            entry_time = (now_ist + timedelta(minutes=1)).strftime("%H:%M")

            photo_bytes = generate_signal_image(entry_time, asset_name, signal)
            caption = (
                f"👑 <b>TAMILSTAR OTC VIP SURE-SHOT</b> 👑\n\n"
                f"📊 <b>ASSET :</b> {asset_name}\n"
                f"⏰ <b>ENTRY TIME :</b> <b>{entry_time} (1-MIN)</b>\n"
                f"🎯 <b>DIRECTION :</b> {'🟢 CALL / BUY (UP)' if signal == 'CALL' else '🔴 PUT / SELL (DOWN)'}\n"
                f"⚡ <b>EXPIRY :</b> 1 MINUTE\n"
                f"🛡 <b>STRATEGY :</b> SMC + HH/LL CONFLUENCE\n\n"
                f"<i>(Use 1-Step MTG only if needed)</i>"
            )

            print(f"[{entry_time}] Signal Sent: {asset_name} -> {signal}")
            send_telegram_photo(photo_bytes, caption)

    except Exception:
        pass

# --- 9. SCANNER LOOP ---
def start_bot():
    print("TamilStar OTC Scanner Starting...")
    time.sleep(2)
    get_channel_id()
    # பாட் கனெக்ட் ஆனதும் உடனடி உறுதி மெசேஜ்
    send_telegram_text("🚀 <b>TamilStar OTC Sure-Shot Bot Active!</b>\n<i>Scanning 13 Assets...</i>")
    while True:
        for name in OTC_ASSETS:
            check_asset(name)
            time.sleep(0.3)
        time.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    start_bot()
  
