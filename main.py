import io
import requests
from datetime import datetime, timedelta
import pytz
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont

BOT_TOKEN = "8837639367:AAEQTwjnl9Ed9Pg9Ln3r6GS1WIjnSlClzG8"
IST = pytz.timezone('Asia/Kolkata')
discovered_chat_id = None
last_alert_minute = ""

app = Flask(__name__)

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

    is_call = (signal_type.upper() == "CALL" or signal_type.upper() == "BUY")
    theme_color = "#00C853" if is_call else "#D50000"
    clean_asset = asset_name.replace("/", " ").replace(" (OTC)", "")

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

def send_telegram_photo(photo_bytes, caption):
    global discovered_chat_id
    cid = discovered_chat_id or get_channel_id()
    if not cid:
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    files = {"photo": ("signal.png", photo_bytes, "image/png")}
    data = {"chat_id": cid, "caption": caption, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=data, files=files, timeout=10)
        return r.status_code == 200
    except Exception:
        return False

@app.route('/')
def home():
    return "TamilStar Master 90% Price Action Webhook Engine Live!"

@app.route('/webhook', methods=['POST'])
def webhook():
    global last_alert_minute
    try:
        data = request.json or request.get_json(force=True)
        if not data:
            return jsonify({"status": "no data"}), 400

        now_ist = datetime.now(IST)
        curr_min = now_ist.strftime("%Y-%m-%d %H:%M")
        if curr_min == last_alert_minute:
            return jsonify({"status": "cooldown"}), 200

        asset = data.get("asset", "EUR/USD")
        signal = data.get("signal", "CALL").upper()
        strategy = data.get("strategy", "SMC + 4th Alternation Confluence")
        
        # 1-Min Prior 24-Hour Entry Time
        entry_time = (now_ist + timedelta(minutes=1)).strftime("%H:%M")

        photo_bytes = generate_signal_image(entry_time, asset, signal)
        caption = (
            f"👑 <b>TAMILSTAR VIP MASTER SURE-SHOT</b> 👑\n\n"
            f"📊 <b>ASSET :</b> {asset}\n"
            f"⏰ <b>ENTRY TIME :</b> <b>{entry_time} (1-MIN)</b>\n"
            f"🎯 <b>DIRECTION :</b> {'🟢 CALL / BUY (UP)' if signal == 'CALL' else '🔴 PUT / SELL (DOWN)'}\n"
            f"⚡ <b>EXPIRY :</b> 1 MINUTE\n"
            f"🛡 <b>CONFLUENCE :</b> {strategy}\n\n"
            f"<i>(Use 1-Step MTG only if needed)</i>"
        )

        send_telegram_photo(photo_bytes, caption)
        last_alert_minute = curr_min
        return jsonify({"status": "success", "signal": signal}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    get_channel_id()
    app.run(host='0.0.0.0', port=8080)
                  
