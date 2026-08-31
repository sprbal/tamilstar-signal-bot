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
    return "TamilStar Red-Green Master OTC Bot Live!"

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

    # Top Details
    draw.text((width / 2, 80), time_str, fill=theme_color, font=font_time, anchor="mm")
    draw.text((width / 2, 160), clean_asset, fill=theme_color, font=font_asset, anchor="mm")

    # Mega Giant Arrow
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

# --- 6. CANDLE HISTORY SIMULATION ENGINE ---
def get_candle_history(asset):
    if asset not in price_store:
        price_store[asset] = {
            'price': 100.0 + np.random.uniform(10, 80),
            'trend': np.random.choice([1, -1])
        }

    st = price_store[asset]
    curr = st['price']

    candles = []
    for _ in range(25):
        bias = np.random.choice([0.15, -0.15])
        o = curr
        c = o + bias + np.random.normal(0, 0.04)
        h = max(o, c) + abs(np.random.normal(0, 0.02))
        l = min(o, c) - abs(np.random.normal(0, 0.02))
        candles.append({'Open': o, 'High': h, 'Low': l, 'Close': c})
        curr = c

    st['price'] = curr
    return pd.DataFrame(candles)

# --- 7. ADVANCED RED-GREEN PATTERN SCANNER ---
def check_asset(asset_name):
    global trade_active_until, last_sent_minute
    try:
        now_ts = time.time()
        if now_ts < trade_active_until:
            return

        now_ist = datetime.now(IST)
        current_minute_str = now_ist.strftime("%Y-%m-%d %H:%M")
        if current_minute_str == last_sent_minute:
            return

        df = get_candle_history(asset_name)
        if df is None or len(df) < 12:
            return

        def get_color(row):
            return "G" if row['Close'] >= row['Open'] else "R"

        # கடைசி 6 கேண்டில்களின் நிறங்கள் (c1 தான் இப்போது முடிந்த சமீபத்திய கேண்டில்)
        c1 = get_color(df.iloc[-1])
        c2 = get_color(df.iloc[-2])
        c3 = get_color(df.iloc[-3])
        c4 = get_color(df.iloc[-4])
        c5 = get_color(df.iloc[-5])
        c6 = get_color(df.iloc[-6])

        signal = None
        strategy_desc = ""

        # --- STRATEGY 1: 4TH CANDLE ALTERNATION ENTRY ---
        # A: Momentum Green [G, G] -> பிறகு [R, G, R] முடிந்துள்ளது -> 4வது கேண்டில் CALL (Green)
        if (c5 == "G" and c4 == "G") and (c3 == "R" and c2 == "G" and c1 == "R"):
            signal = "CALL"
            strategy_desc = "Green Momentum -> R-G-R -> 4th Candle CALL"

        # B: Momentum Red [R, R] -> பிறகு [G, R, G] முடிந்துள்ளது -> 4வது கேண்டில் PUT (Red)
        elif (c5 == "R" and c4 == "R") and (c3 == "G" and c2 == "R" and c1 == "G"):
            signal = "PUT"
            strategy_desc = "Red Momentum -> G-R-G -> 4th Candle PUT"

        # --- STRATEGY 2: DOUBLE COLOR BREAK REVERSAL ENTRY ---
        # C: R-G-R போய்க்கொண்டிருக்கும்போது சடனாக 2 Red [R, R] வந்தால் -> அடுத்த கேண்டில் CALL (Green)
        elif (c4 == "R" and c3 == "G") and (c2 == "R" and c1 == "R"):
            signal = "CALL"
            strategy_desc = "Alternation Break (R-R Trap) -> Reversal CALL"

        # D: G-R-G போய்க்கொண்டிருக்கும்போது சடனாக 2 Green [G, G] வந்தால் -> அடுத்த கேண்டில் PUT (Red)
        elif (c4 == "G" and c3 == "R") and (c2 == "G" and c1 == "G"):
            signal = "PUT"
            strategy_desc = "Alternation Break (G-G Trap) -> Reversal PUT"

        if signal:
            last_sent_minute = current_minute_str
            trade_active_until = now_ts + 120  # 2 நிமிடம் கூல்டவுன் லாக்

            # 1 நிமிடம் முன்னதாக 24-Hour Railway Time என்ட்ரி அலர்ட்
            entry_time = (now_ist + timedelta(minutes=1)).strftime("%H:%M")

            photo_bytes = generate_signal_image(entry_time, asset_name, signal)
            caption = (
                f"👑 <b>TAMILSTAR OTC VIP SURE-SHOT</b> 👑\n\n"
                f"📊 <b>ASSET :</b> {asset_name}\n"
                f"⏰ <b>ENTRY TIME :</b> <b>{entry_time} (1-MIN)</b>\n"
                f"🎯 <b>DIRECTION :</b> {'🟢 CALL / BUY (UP)' if signal == 'CALL' else '🔴 PUT / SELL (DOWN)'}\n"
                f"⚡ <b>EXPIRY :</b> 1 MINUTE\n"
                f"🔥 <b>PATTERN :</b> {strategy_desc}\n\n"
                f"<i>(Use 1-Step MTG only if needed)</i>"
            )

            print(f"[{entry_time}] Signal Sent: {asset_name} -> {signal} ({strategy_desc})")
            send_telegram_photo(photo_bytes, caption)

    except Exception:
        pass

# --- 8. SCANNER LOOP ---
def start_bot():
    print("TamilStar Red-Green & Double-Break Engine Live...")
    time.sleep(2)
    get_channel_id()
    while True:
        for name in OTC_ASSETS:
            check_asset(name)
            time.sleep(0.3)
        time.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    start_bot()
  
