import time
import datetime
import requests
import random
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = "8837639367:AAEQTwjnl9Ed9Pg9Ln3r6GS1WIjnSlClzG8"
CHAT_ID = "@tamilstar_otcbot"

# நீங்கள் குறிப்பிட்ட 13 பிரத்யேக OTC ஜோடிகள்
OTC_PAIRS = [
    "USD/MXN (OTC)", "USD/BRL (OTC)", "USD/PKR (OTC)", "USD/COP (OTC)",
    "USD/BDT (OTC)", "USD/PHP (OTC)", "USD/IDR (OTC)", "USD/DZD (OTC)",
    "USD/ARS (OTC)", "USD/INR (OTC)", "USD/ZAR (OTC)", "USD/NGN (OTC)",
    "USD/EGP (OTC)"
]

# சர்வர் தூங்காமல் 24/7 இயங்க வெப் சர்வர்
class SimpleServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"<h1>Tamilstar VIP Bot is Running 24/7 Live!</h1>")

    def log_message(self, format, *args):
        return

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleServer)
    print(f"Web server started on port {port}")
    server.serve_forever()

def get_india_time():
    utc_now = datetime.datetime.utcnow()
    return utc_now + datetime.timedelta(hours=5, minutes=30)

def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Telegram Error: {e}")
        return False

def run_bot():
    print("தமிழ் ஸ்டார் விஐபி பாட் இயங்குகிறது...")
    
    while True:
        try:
            pair = random.choice(OTC_PAIRS)
            now = get_india_time()
            
            # ரயில்வே நேர வடிவம் (24 Hours) - 1 நிமிடம் முன்னதாக
            entry_dt = now + datetime.timedelta(minutes=1)
            entry_time_str = entry_dt.strftime("%H:%M")
            
            direction = "CALL 🟢 (BUY)" if (now.second % 2 == 0) else "PUT 🔴 (SELL)"

            # சிக்னல் மெசேஜ்
            signal_msg = (
                "⭐ <b>தமிழ் ஸ்டார் விஐபி சிக்னல்</b> ⭐\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                f"📊 <b>அசெட்:</b> {pair}\n"
                f"⏰ <b>என்ட்ரி நேரம்:</b> {entry_time_str} (1 Min)\n"
                f"🎯 <b>டைரக்ஷன்:</b> {direction}\n"
                "🔄 <b>மார்டிங்கேல்:</b> Max 1-Step MTG\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                f"⏳ <i>முன்கூட்டியே அனுப்பப்பட்டுள்ளது! {entry_time_str}:00 தொடங்கும் போது ட்ரேட் எடுக்கவும்.</i>\n\n"
                "⚠️ <b>ட்ரேடிங் விதிகள்:</b>\n"
                "• முதல் கேண்டில் லாஸ் ஆனால் MTG-1 எடுக்கவும்\n"
                "• Doji / பெரிய விக் வந்தால் தவிர்க்கவும்\n"
                "• மணி மேனேஜ்மென்ட் கட்டாயம் பின்பற்றவும்"
            )

            send_telegram_msg(signal_msg)
            print(f"[{entry_time_str}] சிக்னல் அனுப்பப்பட்டது: {pair}")

            # சிக்னல் முடிந்து அடுத்த சிக்னலுக்கு 3 நிமிடங்கள் இடைவெளி
            time.sleep(180)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
    run_bot()
  
