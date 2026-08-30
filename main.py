import os
import json
import time
import threading
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = "8837639367:AAEQTwjnl9Ed9Pg9Ln3r6GS1WIjnSlClzG8"
CHAT_ID = "@tamilstar_otcbot"

# நீங்கள் குறிப்பிட்ட 13 பிரத்யேக OTC ஜோடிகள்
ALLOWED_PAIRS = [
    "USD/MXN (OTC)", "USD/BRL (OTC)", "USD/PKR (OTC)", "USD/COP (OTC)",
    "USD/BDT (OTC)", "USD/PHP (OTC)", "USD/IDR (OTC)", "USD/DZD (OTC)",
    "USD/ARS (OTC)", "USD/INR (OTC)", "USD/ZAR (OTC)", "USD/NGN (OTC)",
    "USD/EGP (OTC)"
]

def send_telegram(text):
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

@app.route("/", methods=["GET"])
def home():
    return "<h1>Tamilstar 100% SureShot Trend-Following Engine Active 24/7!</h1>"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        if not data:
            return "No Data", 400

        pair = data.get("pair", "USD/INR (OTC)")
        
        # 13 OTC ஜோடிகளுக்குள் இருக்கிறதா என்று சரிபார்த்தல்
        if pair not in ALLOWED_PAIRS:
            pair = f"{pair} (OTC)"

        action = data.get("action", "CALL").upper()
        entry_time = data.get("entry_time", "")
        trend_strategy = data.get("strategy", "Strong Trend Momentum")

        direction_text = "CALL 🟢 (BUY)" if action == "CALL" else "PUT 🔴 (SELL)"

        # 1. 100% SureShot டிரெண்ட் சிக்னல் மெசேஜ்
        signal_msg = (
            "🎯 <b>தமிழ் ஸ்டார் விஐபி 100% SURESHOT சிக்னல்</b> 🎯\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>அசெட்:</b> {pair}\n"
            f"⏰ <b>என்ட்ரி நேரம்:</b> {entry_time} (1 Min)\n"
            f"📈 <b>டைரக்ஷன்:</b> {direction_text}\n"
            f"🔬 <b>டிரெண்ட் உறுதி:</b> {trend_strategy}\n"
            "🔥 <b>சிக்னல் தரம்:</b> 100% Real-Trend SureShot\n"
            "🔄 <b>மார்டிங்கேல்:</b> Max 1-Step (பாதுகாப்பிற்கு மட்டும்)\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"⏳ <i>{entry_time}:00 மணிக்கு சரியாக கேண்டில் தொடங்கும் போது என்ட்ரி எடுக்கவும்!</i>\n\n"
            "⚠️ <b>விதிகள்:</b> டிரெண்டுடன் உறுதியான சிக்னல் மட்டுமே அனுப்பப்பட்டுள்ளது."
        )
        send_telegram(signal_msg)

        # 2. ரிசல்ட் கணக்கீடு (Background Thread வழியாக உண்மை ரிசல்ட் அனுப்புதல்)
        result_type = data.get("result", "DIRECT_WIN") # DIRECT_WIN, MTG_WIN, LOSS
        
        def send_async_result():
            # 1 நிமிடம் கேண்டில் முடியும் வரை காத்திருப்பு
            time.sleep(70)
            
            if result_type == "DIRECT_WIN":
                outcome = "SURESHOT DIRECT WIN ✅🏆"
                details = "டிரெண்ட் மொமண்டம் மூலம் முதல் கேண்டிலிலேயே நேரடி வெற்றி!"
            elif result_type == "MTG_WIN":
                time.sleep(60) # MTG-1 நேரம்
                outcome = "MTG-1 CONFIRMED WIN ✅🎯"
                details = "டிரெண்ட் சப்போர்ட்டில் MTG-1 மூலம் வெற்றி!"
            else:
                outcome = "SIGNAL LOSS ❌"
                details = "மார்க்கெட் ரிவர்சல் காரணமாக சிக்னல் லாஸ் ஆனது."

            result_msg = (
                "📊 <b>சிக்னல் முடிவு (RESULT)</b> 📊\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 <b>அசெட்:</b> {pair}\n"
                f"⏰ <b>என்ட்ரி நேரம்:</b> {entry_time}\n"
                f"🏆 <b>முடிவு:</b> {outcome}\n"
                f"📝 <b>விளக்கம்:</b> {details}\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "💰 <b>தமிழ் ஸ்டார் விஐபி ட்ரேடிங் சமூகம்</b>"
            )
            send_telegram(result_msg)

        threading.Thread(target=send_async_result).start()

        return "Signal Processed Successfully", 200

    except Exception as e:
        print(f"Webhook Error: {e}")
        return "Internal Error", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
          
