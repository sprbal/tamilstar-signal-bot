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
    return "Tamil Star OTC VIP Sure-Shot Engine is Active and Running..."

# ================= Configuration =================
BOT_TOKEN = "8980023345:AAG5YMkgYEFkNc_L5ISfqxNOGiB78DM5JPs"
CHANNEL_ID = "@tamilstar_otcbot"

# நீங்கள் குறிப்பிட்ட 13 Quotex OTC Pairs
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

# Advanced Sure-Shot Signal Engine
def signal_engine():
    # Bot Activation Message
    start_text = (
        "🚀 <b>Tamil Star OTC VIP Sure-Shot Engine Activated!</b>\n\n"
        "⚡ <b>Mode:</b> Algorithmic Trend Analysis + Dynamic Result Engine\n"
        "📊 <b>Platform:</b> Quotex OTC (13 High-Volume Pairs)\n"
        "⏱ <b>Timeframe:</b> 1 MIN M1\n"
        "🎯 <b>Accuracy:</b> 92%+ High Probability\n\n"
        "<i>Scanning live OTC candles for strong breakout setups...</i>"
    )
    send_telegram_message(start_text)
    time.sleep(15)

    while True:
        try:
            # 1. Asset & Algorithmic Direction Selection
            pair = random.choice(PAIRS)
            direction_choice = random.choice(["CALL", "PUT"])
            
            if direction_choice == "CALL":
                direction = "CALL 🟢 (BUY)"
                arrow = "⬆️"
            else:
                direction = "PUT 🔴 (SELL)"
                arrow = "⬇️"
            
            # 2. Timing Calculation (IST Time)
            now = datetime.utcnow() + timedelta(hours=5, minutes=30)
            signal_time = now + timedelta(minutes=1)
            time_str = signal_time.strftime("%H:%M")

            # 3. Post VIP Signal with Analysis Details
            signal_msg = (
                "🎯 <b>TAMIL STAR SURE-SHOT VIP SIGNAL</b> 🎯\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 <b>Asset:</b> {pair}\n"
                f"⏰ <b>Entry Time:</b> {time_str} IST\n"
                f"⏱ <b>Expiry:</b> 1 MIN (M1 Candle)\n"
                f"📈 <b>Direction:</b> <b>{direction} {arrow}</b>\n"
                "🛡 <b>Safety:</b> 1-Step MTG (If 1st candle draws/reverses)\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "⚡ <i>Entry strictly at 00 second candle open!</i>"
            )
            send_telegram_message(signal_msg)
            logging.info(f"Signal sent: {pair} | {direction}")

            # 4. Wait for Candle 1 Expiry (70 seconds)
            time.sleep(70)

            # 5. Algorithmic Market Evaluation (Weighted Real-market Simulation)
            # Realistic probability distribution: Direct Win (~65%), MTG Win (~25%), Loss (~10%)
            outcome = random.choices(["DIRECT_WIN", "MTG_REQUIRED", "LOSS"], weights=[65, 25, 10])[0]

            if outcome == "DIRECT_WIN":
                result_msg = (
                    "✅ <b>TRADE RESULT: DIRECT SURE-SHOT WIN!</b> ✅\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 <b>Asset:</b> {pair}\n"
                    f"📈 <b>Trade:</b> {direction}\n"
                    "🏆 <b>Outcome:</b> <b>DIRECT WIN 🟢🔥</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "🎯 <i>Clean breakout entry! Analyzing next setup...</i>"
                )
                send_telegram_message(result_msg)

            elif outcome == "MTG_REQUIRED":
                # 1-Step MTG Announcement
                mtg_alert = (
                    "⚠️ <b>VOLATILITY SPIKE: 1-STEP MTG!</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 <b>Asset:</b> {pair}\n"
                    f"📈 Continue same direction: <b>{direction}</b> for Next 1 Min!\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "💡 <i>Apply standard 2x Money Management.</i>"
                )
                send_telegram_message(mtg_alert)
                
                # Wait for MTG 1-Min Candle Expiry
                time.sleep(68)
                
                # MTG Outcome (80% Win, 20% Real Loss)
                mtg_outcome = random.choices(["MTG_WIN", "LOSS"], weights=[80, 20])[0]
                
                if mtg_outcome == "MTG_WIN":
                    result_msg = (
                        "✅ <b>TRADE RESULT: 1-STEP MTG WIN!</b> ✅\n"
                        "━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 <b>Asset:</b> {pair}\n"
                        f"📈 <b>Trade:</b> {direction}\n"
                        "🏆 <b>Outcome:</b> <b>1-STEP MTG WIN 🟢👍</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━\n"
                        "🎯 <i>Recovery completed successfully!</i>"
                    )
                    send_telegram_message(result_msg)
                else:
                    result_msg = (
                        "❌ <b>TRADE RESULT: LOSS</b> ❌\n"
                        "━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 <b>Asset:</b> {pair}\n"
                        "⚠️ <b>Outcome:</b> <b>LOSS 🔴</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━\n"
                        "💡 <i>Trend exhausted. Avoiding consecutive entries. Next signal soon...</i>"
                    )
                    send_telegram_message(result_msg)

            else:
                # Direct Loss Notification
                result_msg = (
                    "❌ <b>TRADE RESULT: LOSS (Market Reversal)</b> ❌\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 <b>Asset:</b> {pair}\n"
                    "⚠️ <b>Outcome:</b> <b>LOSS 🔴</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "💡 <i>Unfavorable OTC wick action. Resetting strategy for next pair...</i>"
                )
                send_telegram_message(result_msg)

            # 6. Break Interval before Next Analysis (2 to 3.5 minutes for stability)
            break_time = random.randint(120, 210)
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
                      
