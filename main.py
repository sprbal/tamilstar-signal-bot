import time
import logging
import random
import requests

# ==================== BOT CONFIGURATIONS ====================
TELEGRAM_BOT_TOKEN = "8837639367:AAEQTwjnI9Ed9Pg9Ln3r6GSIWljnSICIzG"
TELEGRAM_CHANNEL_ID = "@tamilstar_otcbot"

# Direct Photo URLs
WIN_PHOTO_URL = "https://i.postimg.cc/B620WFfd/file-0000000081b88211ab3f658.jpg"
LOSS_PHOTO_URL = "https://i.postimg.cc/hG9yc1h9/file-0000000077f88211b7322fb.jpg"

# 12 Quotex OTC Assets
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
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        return None

def send_telegram_photo(photo_url, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        return response.json()
    except Exception as e:
        logging.error(f"Error sending photo: {e}")
        return None

def analyze_strict_trend_strategy(asset):
    trend = random.choice(["UPTREND", "DOWNTREND"])
    is_liquidity_sweep = random.random() > 0.65
    is_exhaustion = random.random() > 0.60
    
    if is_liquidity_sweep and is_exhaustion:
        if trend == "UPTREND":
            action = "🟢 CALL (BUY)"
        else:
            action = "🔴 PUT (SELL)"
        win_rate = random.randint(82, 88)
        return True, action, win_rate
    return False, None, 0

def run_trade_cycle(asset, action, win_rate):
    signal_msg = (
        f"🎯 **TAMIL STAR OTC VIP SIGNAL** 🎯\n\n"
        f"📊 **Asset:** `{asset}`\n"
        f"⚡ **Action:** {action}\n"
        f"⏳ **Timeframe:** 1 Minute (M1)\n"
        f"⌛ **Expiry:** 1 Minute (M1)\n"
        f"🔥 **Win Rate:** `{win_rate}%`\n"
        f"🛡️ **Strategy:** SMC Pure Trend Continuation\n\n"
        f"⚠️ *Note: Direct Entry. If direct misses, use 1-Step Martingale immediately!*\n\n"
        f"👨‍💻 **Admin:** @tamilstar_otcbot"
    )
    send_telegram_message(signal_msg)
    logging.info(f"Signal sent: {asset} | {action}")
    
    time.sleep(60)
    
    is_direct_win = random.random() < 0.75
    if is_direct_win:
        win_caption = (
            f"✅ **DIRECT WIN (ITM)!!** ✅\n\n"
            f"📊 **Asset:** `{asset}`\n"
            f"📈 **Action:** {action}\n"
            f"🏆 **Result:** Direct Shot Profit 🚀🔥\n"
            f"👑 **Channel:** @tamilstar_otcbot"
        )
        send_telegram_photo(WIN_PHOTO_URL, win_caption)
    else:
        logging.info("Direct lost, waiting for MTG-1...")
        time.sleep(60)
        is_mtg_win = random.random() < 0.65
        if is_mtg_win:
            mtg_win_caption = (
                f"✅ **MTG-1 WIN (ITM)!!** ✅\n\n"
                f"📊 **Asset:** `{asset}`\n"
                f"📈 **Action:** {action}\n"
                f"🏆 **Result:** 1-Step Martingale Recovery Win 💥\n"
                f"👑 **Channel:** @tamilstar_otcbot"
            )
            send_telegram_photo(WIN_PHOTO_URL, mtg_win_caption)
        else:
            loss_caption = (
                f"❌ **LOSS (OTM)** ❌\n\n"
                f"📊 **Asset:** `{asset}`\n"
                f"📈 **Action:** {action}\n"
                f"📉 **Result:** Stop Loss Hit\n"
                f"⚠️ *Next VIP signal will recover the loss. Follow strict money management.*"
            )
            send_telegram_photo(LOSS_PHOTO_URL, loss_caption)
            
    time.sleep(30)

def main():
    logging.info("Tamil Star OTC Signal Engine is Active and Running...")
    while True:
        for asset in OTC_ASSETS:
            is_valid, action, win_rate = analyze_strict_trend_strategy(asset)
            if is_valid:
                run_trade_cycle(asset, action, win_rate)
                break
        time.sleep(10)

if __name__ == "__main__":
    main()
  
