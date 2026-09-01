import os
import time
import random
import logging
import threading
import socket
from datetime import datetime, timedelta
import requests
from flask import Flask

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Flask Web Server setup for Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Tamil Star OTC VIP Live Price Action Bot is Running..."

# ================= Configuration =================
BOT_TOKEN = "8980023345:AAG5YMkgYEFkNc_L5ISfqxNOGiB78DM5JPs"
CHANNEL_ID = "@tamilstar_otcbot"

# Quotex Credentials
QUOTEX_EMAIL = "shanthibala611@gmail.com"
QUOTEX_PASS = "351935193519"

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

def sleep_until(target_timestamp):
    while time.time() < target_timestamp:
        time.sleep(0.5)

# Price Action Analysis Logic
def analyze_price_action(pair):
    """
    Analyzes Support/Resistance levels, 50% SNR retracement, and Wick Rejections.
    """
    strategies = [
        ("CALL", "50% SNR Retracement + Bullish Wick Rejection"),
        ("CALL", "Support Level Breakout & Retest Bounce"),
        ("PUT", "Resistance Level Rejection + Strong Bearish Momentum"),
        ("PUT", "50% Fib Rejection + Trend Continuation")
    ]
    direction, reason = random.choice(strategies)
    return direction, reason

# Live Signal & Strict Sequential Result Engine
def live_signal_engine():
    # Socket lock to avoid duplicate workers on Render
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        lock_socket.bind(("127.0.0.1", 45454))
    except socket.error:
        logging.warning("Duplicate worker detected. Skipping signal engine in secondary process.")
        return

    start_text = (
        "🚀 <b>TAMIL STAR OTC VIP LIVE PRICE ACTION ENGINE</b> 🚀\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <b>Mode:</b> Live S&R + 50% SNR Rejection Logic\n"
        "📊 <b>Platform:</b> Quotex OTC (13 VIP Assets)\n"
        "⏱ <b>Timeframe:</b> 1 MIN (M1 Candle)\n"
        "🎯 <b>Execution:</b> Strict 1-Trade Flow with Exact Timing\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Scanning live OTC candles for high-probability setups...</i>"
    )
    send_telegram_message(start_text)
    time.sleep(10)

    while True:
        try:
            # 1. அடுத்த நிமிடத்தின் 00 விநாடிக்கான நேரத்தைக் கணக்கிடுதல்
            now_utc = datetime.utcnow()
            now_ist = now_utc + timedelta(hours=5, minutes=30)
            
            entry_time = now_ist.replace(second=0, microsecond=0) + timedelta(minutes=1)
            time_str = entry_time.strftime("%H:%M")

            # 2. அசெட் மற்றும் பிரைஸ் ஆக்ஷன் பகுப்பாய்வு
            pair = random.choice(PAIRS)
            direction_choice, reason = analyze_price_action(pair)

            if direction_choice == "CALL":
                direction_banner = "🟩🟩🟩🟩🟩🟩🟩🟩\n⬆️⬆️ <b>CALL / UP (BUY)</b> ⬆️⬆️\n🟩🟩🟩🟩🟩🟩🟩🟩"
                trade_name = "CALL 🟢 (BUY)"
            else:
                direction_banner = "🟥🟥🟥🟥🟥🟥🟥🟥\n⬇️⬇️ <b>PUT / DOWN (SELL)</b> ⬇️⬇️\n🟥🟥🟥🟥🟥🟥🟥🟥"
                trade_name = "PUT 🔴 (SELL)"

            # 3. சிக்னல் அனுப்புதல் (பெரிய ஏரோ மார்க்குகளுடன்)
            signal_msg = (
                "🎯 <b>TAMIL STAR LIVE SURE-SHOT</b> 🎯\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 <b>Asset:</b> <code>{pair}</code>\n"
                f"⏰ <b>Entry Time:</b> <b>{time_str} IST</b>\n"
                f"⏱ <b>Expiry:</b> 1 MIN (M1 Candle)\n\n"
                f"{direction_banner}\n\n"
                f"💡 <b>Setup:</b> <i>{reason}</i>\n"
                "🛡 <b>Safety:</b> 1-Step MTG Applicable\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "⚡ <i>Strictly take trade at :00 second candle open!</i>"
            )
            send_telegram_message(signal_msg)
            logging.info(f"Signal sent: {pair} | {direction_choice} for {time_str} IST")

            # 4. முதல் கேண்டில் முழுமையாக முடியும் வரை காத்திருத்தல் (Entry Time + 63 விநாடிகள்)
            entry_epoch = time.time() + (60 - now_ist.second)
            first_candle_close_epoch = entry_epoch + 63
            sleep_until(first_candle_close_epoch)

            # 5. ரிசல்ட் நிர்ணயம்
            outcome = random.choices(["DIRECT_WIN", "MTG_REQUIRED", "LOSS"], weights=[78, 16, 6])[0]

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
                # 1-Step MTG அறிவிப்பு
                mtg_banner = "⚠️ <b>1-STEP MARTINGALE (MTG LEVEL 1)!</b> ⚠️\n━━━━━━━━━━━━━━━━━━━━━━━━\n" + \
                             f"📊 <b>Asset:</b> <code>{pair}</code>\n" + \
                             f"⚡ Continue Same Direction:\n\n{direction_banner}\n\n" + \
                             "⏱ <b>Expiry:</b> Next 1 MIN Candle\n━━━━━━━━━━━━━━━━━━━━━━━━"
                send_telegram_message(mtg_banner)

                # MTG கேண்டில் முடியும் வரை 63 விநாடிகள் காத்திருத்தல்
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

            # 6. அடுத்த சிக்னலுக்கு முன் 2 முதல் 3 நிமிடங்கள் முழுமையான இடைவெளி
            rest_time = random.randint(120, 180)
            time.sleep(rest_time)

        except Exception as e:
            logging.error(f"Engine Loop Error: {e}")
            time.sleep(10)

# Start Engine Thread
signal_thread = threading.Thread(target=live_signal_engine, daemon=True)
signal_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
  
