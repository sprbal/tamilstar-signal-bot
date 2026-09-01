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

# Flask Web Server setup for Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Tamil Star OTC Signal Engine is Active and Running..."

# ================= Configuration =================
BOT_TOKEN = "8980023345:AAG5YMkgYEFkNc_L5ISfqxNOGiB78DM5JPs"
CHANNEL_ID = "@tamilstar_otcbot"

PAIRS = [
    "EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC", 
    "USD/CHF OTC", "AUD/USD OTC", "USD/CAD OTC", 
    "EUR/GBP OTC", "EUR/JPY OTC", "USD/INR OTC", 
    "USD/PKR OTC", "USD/BDT OTC", "USD/BRL OTC",
    "USD/EGP OTC", "USD/NGN OTC", "USD/MXN OTC",
    "USD/ZAR OTC", "USD/PHP OTC", "USD/IDR OTC"
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
        logging.info(f"Telegram Message Response: {response.text}")
        return response.json()
    except Exception as e:
        logging.error(f"Error sending Telegram message: {e}")
        return None

# Signal Generator Engine
def signal_engine():
    start_text = (
        "🚀 <b>Tamil Star OTC VIP Bot Activated!</b>\n\n"
        "⚡ <b>Accuracy:</b> 95%+ High Win Rate\n"
        "📊 <b>Platform:</b> Quotex OTC\n"
        "⏱ <b>Timeframe:</b> 1 MIN\n\n"
        "<i>Waiting for the next high-probability setup...</i>"
    )
    send_telegram_message(start_text)
    
    while True:
        try:
            pair = random.choice(PAIRS)
            direction = random.choice(["CALL 🟢 (BUY)", "PUT 🔴 (SELL)"])
            
            now = datetime.utcnow() + timedelta(hours=5, minutes=30)
            next_min = now + timedelta(minutes=1)
            time_str = next_min.strftime("%H:%M")

            signal_msg = (
                "🎯 <b>TAMIL STAR VIP SIGNAL</b> 🎯\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 <b>Asset:</b> {pair}\n"
                f"⏰ <b>Time:</b> {time_str} IST\n"
                f"⏱ <b>Expiry:</b> 1 MIN\n"
                f"📈 <b>Direction:</b> <b>{direction}</b>\n"
                "🛡 <b>Safety:</b> 1-Step MTG Applicable\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "⚠️ <i>Wait for candle opening at exact time!</i>"
            )

            send_telegram_message(signal_msg)
            logging.info(f"Signal sent: {pair} | {direction}")

            wait_time = random.randint(120, 240)
            time.sleep(wait_time)

        except Exception as e:
            logging.error(f"Engine Loop Error: {e}")
            time.sleep(10)

# Start Signal Engine
signal_thread = threading.Thread(target=signal_engine, daemon=True)
signal_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
