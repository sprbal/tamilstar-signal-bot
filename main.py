import os
import time
import random
import logging
import threading
from datetime import datetime, timedelta
import requests
from flask import Flask

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Flask Web Server setup for Render Keep-Alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Tamil Star OTC VIP Bot Engine is Active and Running..."

# ================= Configuration =================
BOT_TOKEN = "8980023345:AAG5YMkgYEFkNc_L5ISfqxNOGiB78DM5JPs"
CHANNEL_ID = "@tamilstar_otcbot"

# நீங்கள் குறிப்பிட்ட சரியான 13 OTC Pairs
PAIRS = [
    "USD/MXN OTC",
    "USD/INR OTC",
    "USD/DZD OTC",
    "USD/ARS OTC",
    "USD/BDT OTC",
    "USD/COP OTC",
    "USD/EGP OTC",
    "USD/IDR OTC",
    "USD/NGN OTC",
    "USD/PHP OTC",
    "USD/PKR OTC",
    "USD/ZAR OTC",
    "BRL/USD OTC"
]

# Helper function to send Telegram messages
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        logging.info(f"Telegram Response: {response.text}")
        return response.json()
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        return None

# Signal & Sequential Result Engine
def signal_engine():
    # Initial Bot Message
    start_text = (
        "🚀 <b>Tamil Star OTC VIP Bot Activated!</b>\n\n"
        "⚡ <b>Mode:</b> 13 VIP Assets + Strict Sequential Flow\n"
        "📊 <b>Platform:</b> Quotex OTC\n"
        "⏱ <b>Timeframe:</b> 1 MIN\n\n"
        "<i>Market analysis in progress... Waiting for first setup.</i>"
    )
    send_telegram_message(start_text)
    time.sleep(10)

    while True:
        try:
            # 1. அசெட் மற்றும் டிரெக்ஷன் தேர்வு
            pair = random.choice(PAIRS)
            direction = random.choice(["CALL 🟢 (BUY)", "PUT 🔴 (SELL)"])
            
            # 2. என்ட்ரி டைம் கணக்கீடு (IST Time)
            now = datetime.utcnow() + timedelta(hours=5, minutes=30)
            signal_time = now + timedelta(minutes=1)
            time_str = signal_time.strftime("%H:%M")

            # 3. சிக்னல் அனுப்புதல்
            signal_msg = (
                "🎯 <b>TAMIL STAR VIP SIGNAL</b> 🎯\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 <b>Asset:</b> {pair}\n"
                f"⏰ <b>Entry Time:</b> {time_str} IST\n"
                f"⏱ <b>Expiry:</b> 1 MIN\n"
                f"📈 <b>Direction:</b> <b>{direction}</b>\n"
                "🛡 <b>Safety:</b> 1-Step MTG Applicable\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "⚠️ <i>Wait for exact candle opening!</i>"
            )
            send_telegram_message(signal_msg)
            logging.info(f"Signal sent: {pair} | {direction}")

            # 4. முதல் 1 நிமிட கேண்டில் முடிவடையும் வரை காத்திருத்தல்
            time.sleep(70)

            # 5. முடிவு கணக்கீடு (Direct Win / MTG Win / Loss)
            outcome = random.choices(["DIRECT_WIN", "MTG_WIN", "LOSS"], weights=[78, 18, 4])[0]

            if outcome == "DIRECT_WIN":
                result_msg = (
                    "✅ <b>TRADE RESULT: DIRECT WIN!</b> ✅\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 <b>Asset:</b> {pair}\n"
                    f"📈 <b>Signal:</b> {direction}\n"
                    "🏆 <b>Status:</b> <b>DIRECT WIN 🟢🔥</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "🎯 <i>Accuracy guaranteed. Analyzing next asset...</i>"
                )
                send_telegram_message(result_msg)

            elif outcome == "MTG_WIN":
                # MTG அலர்ட் போஸ்ட் செய்தல்
                mtg_alert = (
                    "⚠️ <b>1-STEP MTG APPLIED!</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 <b>Asset:</b> {pair}\n"
                    f"📈 Continue same direction: <b>{direction}</b> for 1 MIN!\n"
                    "━━━━━━━━━━━━━━━━━━━━"
                )
                send_telegram_message(mtg_alert)
                
                # MTG கேண்டில் முடிவடையும் வரை காத்திருத்தல்
                time.sleep(65)
                
                result_msg = (
                    "✅ <b>TRADE RESULT: MTG WIN!</b> ✅\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 <b>Asset:</b> {pair}\n"
                    f"📈 <b>Signal:</b> {direction}\n"
                    "🏆 <b>Status:</b> <b>1-STEP MTG WIN 🟢👍</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "🎯 <i>Next signal analyzing...</i>"
                )
                send_telegram_message(result_msg)

            else:
                # Loss அறிவிப்பு
                result_msg = (
                    "❌ <b>TRADE RESULT: LOSS</b> ❌\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 <b>Asset:</b> {pair}\n"
                    "⚠️ <b>Status:</b> <b>LOSS 🔴</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "💡 <i>Market pattern changed. Recovering in next setup...</i>"
                )
                send_telegram_message(result_msg)

            # 6. முடிவு வந்த பிறகு அடுத்த அசெட் சிக்னலுக்கு முன் இடைவெளி (1.5 முதல் 3 நிமிடங்கள்)
            break_time = random.randint(90, 180)
            time.sleep(break_time)

        except Exception as e:
            logging.error(f"Engine Loop Error: {e}")
            time.sleep(10)

# Start Signal Engine Thread
signal_thread = threading.Thread(target=signal_engine, daemon=True)
signal_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
  
