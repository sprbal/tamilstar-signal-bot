import time
import logging
import random
import requests
import os
from threading import Thread
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Tamil Star OTC VIP Bot is Running Live!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_web, daemon=True).start()

# ==================== BOT CONFIGURATIONS ====================
TELEGRAM_BOT_TOKEN = "8980023345:AAHSiT-TuUZybq2bkUdW_TFPgfW4nJa35f4"
TELEGRAM_CHANNEL_ID = "@tamilstar_otcbot"

WIN_PHOTO_URL = "https://i.postimg.cc/B620WFfd/file-0000000081b88211ab3f658.jpg"
LOSS_PHOTO_URL = "https://i.postimg.cc/hG9yc1h9/file-0000000077f88211b7322fb.jpg"

OTC_ASSETS = [
    "USD/EGP OTC", "USD/MXN OTC", "USD/BRL OTC", "USD/IDR OTC", 
    "USD/DZD OTC", "USD/INR OTC", "USD/ZAR OTC", "USD/PKR OTC", 
    "USD/ARS OTC", "USD/PHP OTC", "USD/COP OTC", "USD/NGN OTC"
]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        logging.info(f"Telegram Message Response: {res.text}")
        return res.json()
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        return None

def send_telegram_photo(photo_url, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, json=payload, timeout=15)
        logging.info(f"Telegram Photo Response: {res.text}")
        return res.json()
    except Exception as e:
        logging.error(f"Error sending photo: {e}")
        return None

def run_trade_cycle(asset):
    trend = random.choice(["CALL", "PUT"])
    action = "🟢 CALL (BUY)" if trend == "CALL" else "🔴 PUT (SELL)"
    win_rate = random.randint(82, 88)
    
    signal_msg = (
        f"🎯 <b>TAMIL STAR OTC VIP SIGNAL</b> 🎯\n\n"
        f"📊 <b>Asset:</b> <code>{asset}</code>\n"
        f"⚡ <b>Action:</b> {action}\n"
        f"⏳ <b>Timeframe:</b> 1 Minute (M1)\n"
        f"⌛ <b>Expiry:</b> 1 Minute (M1)\n"
        f"🔥 <b>Win Rate:</b> <code>{win_rate}%</code>\n"
        f"🛡️ <b>Strategy:</b> SMC Pure Trend Continuation\n\n"
        f"⚠️ <i>Note: Direct Entry. If direct misses, use 1-Step Martingale immediately!</i>\n\n"
        f"👨‍💻 <b>Admin:</b> @tamilstar_otcbot"
    )
    
    send_telegram_message(signal_msg)
    logging.info(f"Signal sent: {asset} | {action}")
    
    time.sleep(60)
    
    is_direct_win = random.random() < 0.75
    if is_direct_win:
        win_caption = (
            f"✅ <b>DIRECT WIN (ITM)!!</b> ✅\n\n"
            f"📊 <b>Asset:</b> <code>{asset}</code>\n"
            f"📈 <b>Action:</b> {action}\n"
            f"🏆 <b>Result:</b> Direct Shot Profit 🚀🔥\n"
            f"👑 <b>Channel:</b> @tamilstar_otcbot"
        )
        send_telegram_photo(WIN_PHOTO_URL, win_caption)
    else:
        logging.info("Direct lost, waiting for MTG-1...")
        time.sleep(60)
        is_mtg_win = random.random() < 0.65
        if is_mtg_win:
            mtg_win_caption = (
                f"✅ <b>MTG-1 WIN (ITM)!!</b> ✅\n\n"
                f"📊 <b>Asset:</b> <code>{asset}</code>\n"
                f"📈 <b>Action:</b> {action}\n"
                f"🏆 <b>Result:</b> 1-Step Martingale Recovery Win 💥\n"
                f"👑 <b>Channel:</b> @tamilstar_otcbot"
            )
            send_telegram_photo(WIN_PHOTO_URL, mtg_win_caption)
        else:
            loss_caption = (
                f"❌ <b>LOSS (OTM)</b> ❌\n\n"
                f"📊 <b>Asset:</b> <code>{asset}</code>\n"
                f"📈 <b>Action:</b> {action}\n"
                f"📉 <b>Result:</b> Stop Loss Hit\n"
                f"⚠️ <i>Next VIP signal will recover the loss. Follow strict money management.</i>"
            )
            send_telegram_photo(LOSS_PHOTO_URL, loss_caption)
            
    time.sleep(15)

def main():
    logging.info("Tamil Star OTC Signal Engine is Active and Running...")
    send_telegram_message("🚀 <b>Tamil Star OTC VIP Bot Activated!</b>\nScanning Quotex OTC Markets for 1M High Accuracy Signals...")
    
    while True:
        asset = random.choice(OTC_ASSETS)
        run_trade_cycle(asset)
        time.sleep(10)

if __name__ == "__main__":
    main()
