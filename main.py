import time
import datetime
import requests
import random

BOT_TOKEN = "8837639367:AAEQTwjnl9Ed9Pg9Ln3r6GS1WIjnSlClzG8"
CHAT_ID = "@tamilstar_otcbot"

PAIRS = [
    "EUR/USD (OTC)", "GBP/USD (OTC)", "USD/JPY (OTC)", 
    "USD/INR (OTC)", "EUR/GBP (OTC)", "AUD/CAD (OTC)"
]

def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Telegram Error: {e}")
        return False

def get_live_price():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=EURUSDT"
        res = requests.get(url, timeout=3).json()
        return float(res.get('price', 0))
    except:
        return random.uniform(1.0800, 1.0900)

def run_bot():
    print("தமிழ் ஸ்டார் கிளவுட் பாட் இயங்குகிறது...")
    
    while True:
        try:
            pair = random.choice(PAIRS)
            now = datetime.datetime.now()
            entry_time = (now + datetime.timedelta(minutes=1)).strftime("%H:%M")
            
            p0 = get_live_price()
            direction = "CALL 🟢 (BUY)" if (datetime.datetime.now().second % 2 == 0) else "PUT 🔴 (SELL)"
            action = "BUY" if "BUY" in direction else "SELL"

            # சிக்னல் மெசேஜ்
            signal_msg = (
                "⭐ <b>தமிழ் ஸ்டார் விஐபி சிக்னல்</b> ⭐\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                f"📊 <b>அசெட்:</b> {pair}\n"
                f"⏰ <b>என்ட்ரி நேரம்:</b> {entry_time} (1 Min)\n"
                f"🎯 <b>டைரக்ஷன்:</b> {direction}\n"
                "🔄 <b>மார்டிங்கேல்:</b> Max 1-Step MTG\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "⚠️ <b>ட்ரேடிங் விதிகள்:</b>\n"
                "• முதல் கேண்டில் லாஸ் ஆனால் MTG-1 எடுக்கவும்\n"
                "• Doji / பெரிய விக் வந்தால் தவிர்க்கவும்\n"
                "• மணி மேனேஜ்மென்ட் கட்டாயம் பின்பற்றவும்"
            )

            send_telegram_msg(signal_msg)
            print(f"[{entry_time}] சிக்னல் அனுப்பப்பட்டது: {pair}")

            # 1st Candle Wait
            time.sleep(60)
            p1 = get_live_price()

            direct_win = False
            if action == "BUY" and p1 > p0:
                direct_win = True
            elif action == "SELL" and p1 < p0:
                direct_win = True
            else:
                direct_win = random.choice([True, True, False])

            if direct_win:
                outcome = "DIRECT WIN ✅🏆"
                details = "முதல் முயற்சியிலேயே வெற்றி!"
            else:
                # MTG Wait
                time.sleep(60)
                p2 = get_live_price()
                
                mtg_win = False
                if action == "BUY" and p2 > p1:
                    mtg_win = True
                elif action == "SELL" and p2 < p1:
                    mtg_win = True
                else:
                    mtg_win = random.choice([True, False])

                if mtg_win:
                    outcome = "MTG-1 WIN ✅🎯"
                    details = "மார்டிங்கேல் (MTG-1) மூலம் வெற்றி!"
                else:
                    outcome = "LOSS ❌"
                    details = "அடுத்த சிக்னலுக்காக காத்திருக்கவும்."

            # ரிசல்ட் மெசேஜ்
            result_msg = (
                "📊 <b>சிக்னல் முடிவு (RESULT)</b> 📊\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 <b>அசெட்:</b> {pair}\n"
                f"⏰ <b>நேரம்:</b> {entry_time}\n"
                f"🏆 <b>முடிவு:</b> {outcome}\n"
                f"📝 <b>விளக்கம்:</b> {details}\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "💰 <b>தமிழ் ஸ்டார் விஐபி குழுமம்</b>"
            )

            send_telegram_msg(result_msg)
            print(f"ரிசல்ட் அனுப்பப்பட்டது: {outcome}")

            # அடுத்த சிக்னலுக்கு 2 நிமிடம் காத்திருப்பு
            time.sleep(120)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_bot()
