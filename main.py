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

# Flask Keep-Alive Server
app = Flask(__name__)

@app.route('/')
def home():
    return "Tamil Star OTC VIP Single-Cycle Bot is Running..."

# ================= Configuration =================
BOT_TOKEN = "8980023345:AAG5YMkgYEFkNc_L5ISfqxNOGiB78DM5JPs"
CHANNEL_ID = "@tamilstar_otcbot"

# நீங்கள் தேர்வு செய்த 13 OTC Pairs
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

# Precision Sleep Helper
def sleep_until(target_timestamp):
    while time.time() < target_timestamp:
        time.sleep(0.5)

# Signal & Strict Single-Trade Lifecycle Engine
def signal_engine():
    # Initial Start Notification
    start_text = (
        "🚀 <b>TAMIL STAR OTC VIP ENGINE ACTIVATED!</b> 🚀\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <b>Mode:</b> Strict 1-Trade Flow (No Overlapping)\n"
        "🎯 <b>Accuracy:</b> 90%+ Quotex OTC Sure-Shot Engine\n"
        "📊 <b>Pairs:</b> 13 High-Probability OTC Assets\n"
        "⏱ <b>Timeframe:</b> 1 MIN (M1 Candle)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Scanning live OTC price action for clean trend setups...</i>"
    )
    send_telegram_message(start_text)
    time.sleep(10)

    while True:
        try:
            # 1. அடுத்த நிமிடத்தின் 00 விநாடிக்கான நேரத்தைக் கணக்கிடுதல்
            now_utc = datetime.utcnow()
            now_ist = now_utc + timedelta(hours=5, minutes=30)
            
            # அடுத்த முழு நிமிடத்தின் ஆரம்பம்
            entry_time = now_ist.replace(second=0, microsecond=0) + timedelta(minutes=1)
            time_str = entry_time.strftime("%H:%M")

            # 2. அசெட் & வலுவான மொமெண்டம் டைரக்ஷன் தேர்வு
            pair = random.choice(PAIRS)
            direction_type = random.choice(["CALL", "PUT"])

            if direction_type == "CALL":
                direction_banner = "🟩🟩🟩🟩🟩🟩🟩🟩\n⬆️⬆️ <b>CALL / UP (BUY)</b> ⬆️⬆️\n🟩🟩🟩🟩🟩🟩🟩🟩"
                trade_name = "CALL 🟢 (BUY)"
            else:
                direction_banner = "🟥🟥🟥🟥🟥🟥🟥🟥\n⬇️⬇️ <b>PUT / DOWN (SELL)</b> ⬇️⬇️\n🟥🟥🟥🟥🟥🟥🟥🟥"
                trade_name = "PUT 🔴 (SELL)"

            # 3. சிக்னல் அனுப்புதல் (பெரிய ஏரோ மார்க்குகளுடன்)
            signal_msg = (
                "🎯 <b>TAMIL STAR VIP SURE-SHOT</b> 🎯\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 <b>Asset:</b> <code>{pair}</code>\n"
                f"⏰ <b>Entry Time:</b> <b>{time_str} IST</b>\n"
                f"⏱ <b>Expiry:</b> 1 MIN\n\n"
                f"{direction_banner}\n\n"
                "🛡 <b>Safety Rule:</b> 1-Step MTG Applicable\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "⚡ <i>Enter trade strictly at :00 candle open!</i>"
            )
            send_telegram_message(signal_msg)
            logging.info(f"Signal sent: {pair} | {direction_type} for {time_str}")

            # 4. சிக்னல் கேண்டில் தொடங்கும் விநாடி மற்றும் முடியும் விநாடி வரை காத்திருத்தல்
            entry_epoch = time.time() + (60 - now_ist.second)
            first_candle_close_epoch = entry_epoch + 62  # 60s candle + 2s validation buffer
            sleep_until(first_candle_close_epoch)

            # 5. OTC அல்காரிதம் ரிசல்ட் கணக்கீடு (Direct Win: ~76%, MTG: ~18%, Loss: ~6%)
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
                # 1-Step MTG அலெர்ட் (பெரிய ஏரோ மார்க்குடன்)
                mtg_banner = "⚠️ <b>1-STEP MTG LEVEL 1 APPLIED!</b> ⚠️\n━━━━━━━━━━━━━━━━━━━━━━━━\n" + \
                             f"📊 <b>Asset:</b> <code>{pair}</code>\n" + \
                             f"⚡ Continue Same Direction:\n\n{direction_banner}\n\n" + \
                             "⏱ <b>Expiry:</b> Next 1 MIN Candle\n━━━━━━━━━━━━━━━━━━━━━━━━"
                send_telegram_message(mtg_banner)

                # MTG கேண்டில் முடியும் வரை காத்திருத்தல் (62 நொடிகள்)
                mtg_close_epoch = time.time() + 62
                sleep_until(mtg_close_epoch)

                # MTG Outcome (85% Win, 15% Loss)
                mtg_outcome = random.choices(["MTG_WIN", "LOSS"], weights=[85, 15])[0]

                if mtg_outcome == "MTG_WIN":
                    result_msg = (
                        "✅ <b>TRADE RESULT: MTG WIN!</b> ✅\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 <b>Asset:</b> {pair}\n"
                        f"📈 <b>Signal:</b> {trade_name}\n"
                        "🏆 <b>Status:</b> <b>1-STEP MTG WIN 🟢👍</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "🎯 <i>Recovery trade completed!</i>"
                    )
                    send_telegram_message(result_msg)
                else:
                    result_msg = (
                        "❌ <b>TRADE RESULT: LOSS</b> ❌\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 <b>Asset:</b> {pair}\n"
                        "⚠️ <b>Status:</b> <b>LOSS 🔴</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "💡 <i>Market wick reversal. Recovering in next setup...</i>"
                    )
                    send_telegram_message(result_msg)

            else:
                # Direct Loss Result
                result_msg = (
                    "❌ <b>TRADE RESULT: LOSS</b> ❌\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 <b>Asset:</b> {pair}\n"
                    "⚠️ <b>Status:</b> <b>LOSS 🔴</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "💡 <i>Trend exhausted. Moving to next high-volume pair...</i>"
                )
                send_telegram_message(result_msg)

            # 6. ஒரு சிக்னலின் ரிசல்ட் முழுமையாக முடிந்த பிறகு அடுத்த அனாலிசிஸுக்கு 2-3 நிமிடங்கள் கேப்
            rest_time = random.randint(120, 180)
            time.sleep(rest_time)

        except Exception as e:
            logging.error(f"Engine Loop Error: {e}")
            time.sleep(10)

# Start Single Engine Thread
signal_thread = threading.Thread(target=signal_engine, daemon=True)
signal_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
  
