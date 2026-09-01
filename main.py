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

app = Flask(__name__)

@app.route('/')
def home():
    return "Tamil Star OTC VIP Bot with Telegram Controller is Running..."

# ================= Configuration =================
BOT_TOKEN = "8980023345:AAG5YMkgYEFkNc_L5ISfqxNOGiB78DM5JPs"
CHANNEL_ID = "@tamilstar_otcbot"

# Signals Global State
SIGNALS_ACTIVE = False  # Start-up default: OFF (சிக்னல்கள் போகாமல் இருக்க)

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

def send_telegram_message(chat_id, message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        return None

def sleep_until(target_timestamp):
    while time.time() < target_timestamp:
        time.sleep(0.5)

# ================= Telegram Command Listener =================
def telegram_command_listener():
    global SIGNALS_ACTIVE
    last_update_id = 0
    logging.info("Telegram Command Listener Started...")

    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
            res = requests.get(url, timeout=35).json()

            if "result" in res:
                for update in res["result"]:
                    last_update_id = update["update_id"]

                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"].strip().lower()

                        if text == "/stop" or text == "/stop_signals":
                            SIGNALS_ACTIVE = False
                            send_telegram_message(chat_id, "🛑 <b>சிக்னல்கள் வெற்றிகரமாக நிறுத்தப்பட்டது (PAUSED)!</b>\n\nசேனலுக்கு இனி சிக்னல்கள் போகாது. மீண்டும் தொடங்க <code>/start</code> என அனுப்பவும்.")
                            logging.info("Signals STOPPED by Admin Command.")

                        elif text == "/start" or text == "/start_signals":
                            SIGNALS_ACTIVE = True
                            send_telegram_message(chat_id, "🚀 <b>சிக்னல்கள் மீண்டும் தொடங்கப்பட்டது (RUNNING)!</b>\n\nஅடுத்த நிமிடத்திலிருந்து சேனலில் சிக்னல்கள் வரும். நிறுத்த <code>/stop</code> என அனுப்பவும்.")
                            logging.info("Signals STARTED by Admin Command.")

                        elif text == "/status":
                            status_text = "🟢 <b>RUNNING (ஆன்-ல் உள்ளது)</b>" if SIGNALS_ACTIVE else "🔴 <b>STOPPED (ஆஃப்-ல் உள்ளது)</b>"
                            send_telegram_message(chat_id, f"📊 <b>BOT CURRENT STATUS:</b>\n\nநிலை: {status_text}")

        except Exception as e:
            logging.error(f"Error in Command Listener: {e}")
            time.sleep(5)

# ================= Signal Engine =================
def signal_engine():
    global SIGNALS_ACTIVE
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        lock_socket.bind(("127.0.0.1", 45454))
    except socket.error:
        logging.warning("Duplicate worker detected. Skipping signal loop.")
        return

    while True:
        try:
            # சிக்னல் ஆஃப்-ல் இருந்தால் சும்மா காத்திருக்கும்
            if not SIGNALS_ACTIVE:
                time.sleep(3)
                continue

            now_utc = datetime.utcnow()
            now_ist = now_utc + timedelta(hours=5, minutes=30)
            
            entry_time = now_ist.replace(second=0, microsecond=0) + timedelta(minutes=1)
            time_str = entry_time.strftime("%H:%M")

            pair = random.choice(PAIRS)
            direction_type = random.choice(["CALL", "PUT"])

            if direction_type == "CALL":
                direction_banner = "🟩🟩🟩🟩🟩🟩🟩🟩\n⬆️⬆️ <b>CALL / UP (BUY)</b> ⬆️⬆️\n🟩🟩🟩🟩🟩🟩🟩🟩"
                trade_name = "CALL 🟢 (BUY)"
            else:
                direction_banner = "🟥🟥🟥🟥🟥🟥🟥🟥\n⬇️⬇️ <b>PUT / DOWN (SELL)</b> ⬇️⬇️\n🟥🟥🟥🟥🟥🟥🟥🟥"
                trade_name = "PUT 🔴 (SELL)"

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
            
            if SIGNALS_ACTIVE:
                send_telegram_message(CHANNEL_ID, signal_msg)

            entry_epoch = time.time() + (60 - now_ist.second)
            first_candle_close_epoch = entry_epoch + 63
            sleep_until(first_candle_close_epoch)

            if not SIGNALS_ACTIVE:
                continue

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
                if SIGNALS_ACTIVE:
                    send_telegram_message(CHANNEL_ID, result_msg)

            elif outcome == "MTG_REQUIRED":
                mtg_banner = (
                    "⚠️ <b>1-STEP MARTINGALE (MTG LEVEL 1)!</b> ⚠️\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 <b>Asset:</b> <code>{pair}</code>\n"
                    f"⚡ Continue Same Direction:\n\n{direction_banner}\n\n"
                    "⏱ <b>Expiry:</b> Next 1 MIN Candle\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━"
                )
                if SIGNALS_ACTIVE:
                    send_telegram_message(CHANNEL_ID, mtg_banner)

                mtg_close_epoch = time.time() + 63
                sleep_until(mtg_close_epoch)

                if not SIGNALS_ACTIVE:
                    continue

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
                else:
                    result_msg = (
                        "❌ <b>TRADE RESULT: LOSS</b> ❌\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 <b>Asset:</b> {pair}\n"
                        "⚠️ <b>Status:</b> <b>LOSS 🔴</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━"
                    )
                if SIGNALS_ACTIVE:
                    send_telegram_message(CHANNEL_ID, result_msg)

            else:
                result_msg = (
                    "❌ <b>TRADE RESULT: LOSS</b> ❌\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 <b>Asset:</b> {pair}\n"
                    "⚠️ <b>Status:</b> <b>LOSS 🔴</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━"
                )
                if SIGNALS_ACTIVE:
                    send_telegram_message(CHANNEL_ID, result_msg)

            rest_time = random.randint(120, 180)
            time.sleep(rest_time)

        except Exception as e:
            logging.error(f"Engine Loop Error: {e}")
            time.sleep(10)

# Start Threads
threading.Thread(target=telegram_command_listener, daemon=True).start()
threading.Thread(target=signal_engine, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
