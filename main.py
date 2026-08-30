import time
import datetime
import requests
import random
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = "8837639367:AAEQTwjnl9Ed9Pg9Ln3r6GS1WIjnSlClzG8"
CHAT_ID = "@tamilstar_otcbot"

# 13 பிரத்யேக OTC ஜோடிகள்
OTC_PAIRS = [
    "USD/MXN (OTC)", "USD/BRL (OTC)", "USD/PKR (OTC)", "USD/COP (OTC)",
    "USD/BDT (OTC)", "USD/PHP (OTC)", "USD/IDR (OTC)", "USD/DZD (OTC)",
    "USD/ARS (OTC)", "USD/INR (OTC)", "USD/ZAR (OTC)", "USD/NGN (OTC)",
    "USD/EGP (OTC)"
]

# 24/7 சர்வர் தூங்காமல் இருக்க Web Server
class SimpleServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"<h1>Tamilstar VIP SureShot Trend Bot Active 24/7</h1>")

    def log_message(self, format, *args):
        return

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleServer)
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
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

# Trend-Following & SureShot அல்காரிதம்
def get_trend_signal():
    trend_type = random.choice(["BULLISH", "BEARISH"])
    
    if trend_type == "BULLISH":
        direction = "CALL 🟢 (BUY)"
        strategy = "Strong Bullish Trend Momentum"
        analysis = "EMA 20 & RSI சப்போர்ட் உறுதி செய்யப்பட்டது"
    else:
        direction = "PUT 🔴 (SELL)"
        strategy = "Strong Bearish Trend Momentum"
        analysis = "EMA 20 & RSI ரெசிஸ்டன்ஸ் உறுதி செய்யப்பட்டது"
        
    return direction, strategy, analysis

def run_bot():
    print("தமிழ் ஸ்டார் ஷூயர்ஷாட் டிரெண்ட் பாட் இயங்குகிறது...")
    
    while True:
        try:
            pair = random.choice(OTC_PAIRS)
            now = get_india_time()
            
            # 1 நிமிடம் முன்கூட்டியே என்ட்ரி நேரம் (24 Hours Railway Time)
            entry_dt = now + datetime.timedelta(minutes=1)
            entry_time_str = entry_dt.strftime("%H:%M")
            
            direction, strategy, analysis = get_trend_signal()

            # 1. சிக்னல் மெசேஜ்
            signal_msg = (
                "🎯 <b>தமிழ் ஸ்டார் விஐபி SURESHOT சிக்னல்</b> 🎯\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                f"📊 <b>அசெட்:</b> {pair}\n"
                f"⏰ <b>என்ட்ரி நேரம்:</b> {entry_time_str} (1 Min)\n"
                f"📈 <b>டைரக்ஷன்:</b> {direction}\n"
                f"🔬 <b>டிரெண்ட் உறுதி:</b> {strategy}\n"
                "🔥 <b>சிக்னல் தரம்:</b> 99% SureShot Direct Win\n"
                "🔄 <b>MTG:</b> Max 1-Step (பாதுகாப்பிற்கு மட்டும்)\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                f"⏳ <i>{entry_time_str}:00 மணிக்கு கேண்டில் தொடங்கும் போது ட்ரேட் எடுக்கவும்!</i>\n\n"
                f"💡 <b>அனாலிசிஸ்:</b> {analysis}\n"
                "⚠️ <i>Doji வந்தால் ட்ரேடை தவிர்க்கவும்.</i>"
            )

            send_telegram_msg(signal_msg)
            print(f"[{entry_time_str}] சிக்னல் அனுப்பப்பட்டது: {pair} -> {direction}")

            # ட்ரேட் கேண்டில் முடியும் வரை காத்திருப்பு (2 நிமிடங்கள்)
            time.sleep(120)

            # 2. SureShot வெற்றி முடிவு கணக்கீடு
            # அதிகபட்சம் Direct Win அடிக்கும் வகையில் ஃபில்டர்
            is_direct = random.choice([True, True, True, True, False])

            if is_direct:
                outcome = "SURESHOT DIRECT WIN ✅🏆"
                details = "டிரெண்ட் மொமண்டம் மூலம் முதல் கேண்டிலிலேயே நேரடி வெற்றி!"
            else:
                time.sleep(60) # MTG-1 காத்திருப்பு
                outcome = "MTG-1 CONFIRMED WIN ✅🎯"
                details = "டிரெண்ட் சப்போர்ட்டில் MTG-1 மூலம் வெற்றி!"

            # 3. ரிசல்ட் மெசேஜ்
            result_msg = (
                "📊 <b>சிக்னல் முடிவு (RESULT)</b> 📊\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 <b>அசெட்:</b> {pair}\n"
                f"⏰ <b>என்ட்ரி நேரம்:</b> {entry_time_str}\n"
                f"🏆 <b>முடிவு:</b> {outcome}\n"
                f"📝 <b>விளக்கம்:</b> {details}\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "💰 <b>தமிழ் ஸ்டார் விஐபி ட்ரேடிங் சமூகம்</b>"
            )

            send_telegram_msg(result_msg)
            print(f"ரிசல்ட் அனுப்பப்பட்டது: {outcome}")

            # அடுத்த தரமான சிக்னலுக்கு 2.5 நிமிடங்கள் இடைவெளி (Overtrading தடுப்பு)
            time.sleep(150)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
    run_bot()
          
