import io
import time
import email
import imaplib
import requests
from datetime import datetime, timedelta
import pytz
from PIL import Image, ImageDraw, ImageFont

# ================= CREDENTIALS =================
BOT_TOKEN = "8837639367:AAEQTwjnl9Ed9Pg9Ln3r6GS1WIjnSlClzG8"
GMAIL_USER = "sprbala76@gmail.com"
GMAIL_PASS = "prmrddzbvdjwsdvv"

IST = pytz.timezone('Asia/Kolkata')
discovered_chat_id = None
last_sent_time = None

# ================= TELEGRAM HANDLER =================
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

    # Header Text
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

# ================= GMAIL IMAP LISTENER =================
def process_tradingview_alert(body_text, subject_text):
    global last_sent_time
    now_ist = datetime.now(IST)

    # 1-Minute Anti-Spam Lock
    if last_sent_time and (now_ist - last_sent_time).total_seconds() < 55:
        return

    entry_time = (now_ist + timedelta(minutes=1)).strftime("%H:%M")
    combined = (subject_text + " " + body_text).upper()
    
    if "CALL" in combined or "BUY" in combined:
        signal = "CALL"
    elif "PUT" in combined or "SELL" in combined:
        signal = "PUT"
    else:
        return

    asset = "GOLD (XAU/USD)" if ("XAU" in combined or "GOLD" in combined) else "EUR/USD"
    for cur in ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "EURGBP", "EURJPY", "GBPJPY"]:
        if cur in combined:
            asset = cur[:3] + "/" + cur[3:]
            break

    strategy = "SMC & 4th Alternation Confluence"
    if "4TH" in combined:
        strategy = "4th Candle Alternation Wave"
    elif "FIB" in combined:
        strategy = "Fibonacci 0.618 Golden Bounce"
    elif "SNR" in combined:
        strategy = "Strong SNR Rejection Level"

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

    if send_telegram_photo(photo_bytes, caption):
        last_sent_time = now_ist

def check_gmail_loop():
    print("TamilStar Spam-Protected Engine Active...")
    get_channel_id()
    while True:
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(GMAIL_USER, GMAIL_PASS)
            mail.select("inbox")

            status, messages = mail.search(None, '(UNSEEN FROM "noreply@tradingview.com")')
            if status == "OK" and messages[0]:
                for num in messages[0].split():
                    # Mark email as read immediately so it never triggers again
                    mail.store(num, '+FLAGS', '\\Seen')
                    
                    status, data = mail.fetch(num, "(RFC822)")
                    for response_part in data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject = str(msg["Subject"])
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    if part.get_content_type() == "text/plain":
                                        body = part.get_payload(decode=True).decode(errors="ignore")
                                        break
                            else:
                                body = msg.get_payload(decode=True).decode(errors="ignore")

                            process_tradingview_alert(body, subject)
            mail.logout()
        except Exception:
            pass
        time.sleep(4)

if __name__ == "__main__":
    check_gmail_loop()
  
