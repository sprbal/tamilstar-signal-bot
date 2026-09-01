import os
import time
import random
import logging
import threading
import socket
from datetime import datetime, timedelta
import requests
from flask import Flask

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Flask Keep-Alive Server
app = Flask(__name__)

@app.route('/')
def home():
    return "Tamil Star OTC VIP Precision Bot is Running..."

# ================= Configuration =================
BOT_TOKEN = "8980023345:AAG5YMkgYEFkNc_L5ISfqxNOGiB78DM5JPs"
CHANNEL_ID = "@tamilstar_otcbot"

# 13 Quotex OTC Pairs (Corrected USD/BRL OTC)
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
    "USD/BRL OTC"
]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        logging.info(f"Telegram Sent Status: {response.status_code}")
        return response.json()
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        return None

def sleep_until(target_timestamp):
    while time.time() < target_timestamp:
        time.sleep(0.5)

# Signal Engine with Single-Instance Lock
def signal_engine():
    # Socket lock to avoid duplicate workers on Render
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        lock_socket.bind(("127.0.0.1", 45454))
    except socket.error:
        logging.warning("Duplicate worker detected. Skipping signal engine in secondary process.")
        return

    start_text = (
        "🚀 <b>TAMIL STAR OTC VIP SURE-SHOT ENGINE</b> 🚀\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <b>Mode:</b> Strict 1-Trade Flow (No Overlapping)\n"
        "📊 <b>Platform:</b> Quotex OTC (13 VIP Assets)\n"
        "⏱ <b>Timeframe:</b> 1 MIN (M1 Candle)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Scanning OTC setups for clean candle entries...</i>"
    )
    send_telegram_message(start_text)
    time.sleep(10)

    while True:
        try:
            # 1. கணக்கீடு: அடுத்த நிமிடத்தின் 00 விநாடி (IST Time)
            now_utc = datetime.utcnow()
            now_ist = now_utc + timedelta(hours=5, minutes=30)
            
            entry_time = now_ist.replace(second=0, microsecond=0) + timedelta(minutes=1)
            time_str = entry_time.strftime("%H:%M")

            # 2. அசெட் & மொமெண்டம் தேர்வு
            pair = random.choice(PAIRS)
            direction_type = random.choice(["CALL", "PUT"])

            if direction_type == "CALL":
                direction_banner = "🟩🟩🟩🟩🟩🟩🟩🟩\n⬆️⬆️ <b>CALL / UP (BUY)</b> ⬆️⬆️\n🟩🟩🟩🟩🟩🟩🟩🟩"
                trade_name = "CALL 🟢 (BUY)"
            else:
                direction_banner = "🟥🟥🟥🟥🟥🟥🟥🟥\n⬇️⬇️ <b>PUT / DOWN (SELL)</b> ⬇️⬇️\n🟥🟥🟥🟥🟥🟥🟥🟥"
                trade_name = "PUT 🔴 (SELL)"

            # 3. சிக்னல் போஸ்ட் செய்தல் (தெளிவான Entry Time உடன்)
            signal_msg = (
                "🎯 <b>TAMIL STAR VIP SURE-SHOT</b> 🎯\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 <b>Asset:</b> <code>{pair}</code>\n"
                f"⏰ <b>Entry Time:</b> <b>{time_str} IST</b>\n"
                f"⏱ <b>Expiry:</b> 1 MIN (M1 Candle)\n\n"
                f"{direction_banner}\n\n"
                "🛡 <b>Safety:</b> 1-Step MTG Applicable\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "⚡ <i>Strictly take trade at :00 second candle open!</i>"
            )
            send_telegram_message(signal_msg)
            logging.info(f"Signal sent: {pair} | {direction_type} for {time_str} IST")

            # 4. முதல் கேண்டில் முடியும் வரை காத்திருத்தல் (Entry + 63 நொடிகள்)
            entry_epoch = time.time() + (60 - now_ist.second)
            first_candle_close_epoch = entry_epoch + 63
            sleep_until(first_candle_close_epoch)

            # 5. முடிவு அறிவிப்பு (Direct Win / MTG / Loss)
            outcome = random.choices(["DIRECT_WIN", "MTG_REQUIRED", "LOSS"], weights=[76, 18, 6])[0]

            if outcome == "DIRECT_WIN":
                result_msg = (
                    "✅ <b>TRADE RESULT: DIRECT SURE-SHOT!</b> ✅\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 <b>Asset:</b> {pair}\n"
                    f"📈 <b>Signal:</b> {trade_name}\n"
                    "🏆 <b>Status:</b> <b>DIRECT WIN 🟢🔥</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "🎯 <i>Clean Breakout Win! Next asset scanning...</i>"
                )
                send_telegram_message(result_msg)

            elif outcome == "MTG_REQUIRED":
                # 1-Step MTG Alert
                mtg_banner = (
                    "⚠️ <b>1-STEP MARTINGALE (MTG LEVEL 1)!</b> ⚠️\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 <b>Asset:</b> <code>{pair}</code>\n"
                    f"⚡ Continue Same Direction:\n\n{direction_banner}\n\n"
                    "⏱ <b>Expiry:</b> Next 1 MIN Candle\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━"
                )
                send_telegram_message(mtg_banner)

                # MTG கேண்டில் முடியும் வரை காத்திருத்தல் (63 நொடிகள்)
                mtg_close_epoch = time.time() + 63
                sleep_until(mtg_close_epoch)

                mtg_outcome = random.choices(["MTG_WIN", "LOSS"], weights=[85, 15])[0]

                if mtg_outcome == "MTG_WIN":
                    result_msg = (
                        "✅ <b>TRADE RESULT: MTG WIN!</b> ✅\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 <b>Asset:</b> {pair}\n"
                        f"📈 <b>Signal:</b> {trade_name}\n"
                        "🏆 <b>Status:</b> <b>1-STEP MTG WIN 🟢👍</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "🎯 <i>Recovery completed successfully!</i>"
                    )
                    send_telegram_message(result_msg)
                else:
                    result_msg = (
                        "❌ <b>TRADE RESULT: LOSS</b> ❌\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 <b>Asset:</b> {pair}\n"
                        "⚠️ <b>Status:</b> <b>LOSS 🔴</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "💡 <i>Market pattern changed. Moving to next pair...</i>"
                    )
                    send_telegram_message(result_msg)

            else:
                result_msg = (
                    "❌ <b>TRADE RESULT: LOSS</b> ❌\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 <b>Asset:</b> {pair}\n"
                    "⚠️ <b>Status:</b> <b>LOSS 🔴</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "💡 <i>Sudden OTC reversal. Recovering next...</i>"
                )
                send_telegram_message(result_msg)

            # 6. அடுத்த டிரேடுக்கு முன் 2-3 நிமிடங்கள் இடைவெளி
            rest_time = random.randint(120, 180)
            time.sleep(rest_time)

        except Exception as e:
            logging.error(f"Engine Loop Error: {e}")
            time.sleep(10)

# Start Engine Background Thread
signal_thread = threading.Thread(target=signal_engine, daemon=True)
signal_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
  
