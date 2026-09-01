import os
import time
import logging
import threading
import socket
from datetime import datetime, timedelta
import requests
from flask import Flask
from quotexpy import Quotex

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Flask Keep-Alive Server for Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Tamil Star OTC VIP Live Quotex Engine is Running..."

# Telegram Configuration
BOT_TOKEN = "8980023345:AAG5YMkgYEFkNc_L5ISfqxNOGiB78DM5JPs"
CHANNEL_ID = "@tamilstar_otcbot"

# Quotex Credentials
QUOTEX_EMAIL = "shanthibala611@gmail.com"
QUOTEX_PASS = "351935193519"

# 13 OTC Pairs in Quotex WebSocket Format
PAIRS = [
    {"display": "USD/MXN OTC", "asset": "USDMXN_otc"},
    {"display": "USD/INR OTC", "asset": "USDINR_otc"},
    {"display": "USD/DZD OTC", "asset": "USDDZD_otc"},
    {"display": "USD/ARS OTC", "asset": "USDARS_otc"},
    {"display": "USD/BDT OTC", "asset": "USDBDT_otc"},
    {"display": "USD/COP OTC", "asset": "USDCOP_otc"},
    {"display": "USD/EGP OTC", "asset": "USDEGP_otc"},
    {"display": "USD/IDR OTC", "asset": "USDIDR_otc"},
    {"display": "USD/NGN OTC", "asset": "USDNGN_otc"},
    {"display": "USD/PHP OTC", "asset": "USDPHP_otc"},
    {"display": "USD/PKR OTC", "asset": "USDPKR_otc"},
    {"display": "USD/ZAR OTC", "asset": "USDZAR_otc"},
    {"display": "USD/BRL OTC", "asset": "USDBRL_otc"}
]

client = None

def get_quotex_client():
    """Initializes and returns a connected Quotex client instance."""
    global client
    try:
        if client is None:
            logging.info("Connecting to Quotex Live WebSocket...")
            client = Quotex(email=QUOTEX_EMAIL, password=QUOTEX_PASS)
            connected, reason = client.connect()
            if connected:
                logging.info("Connected to Quotex WebSocket successfully.")
                client.change_account("PRACTICE")
            else:
                logging.error(f"Failed to connect to Quotex: {reason}")
                client = None
        return client
    except Exception as e:
        logging.error(f"Quotex connection error: {e}")
        client = None
        return None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        return None

def analyze_candles_price_action(candles):
    """
    Live Price Action Math: Support/Resistance, 50% Retracement & Wick Rejections
    """
    if not candles or len(candles) < 10:
        return None, None

    last_candle = candles[-1]
    prev_candles = candles[-10:-1]

    highs = [c.get('high', c.get('h', 0)) for c in prev_candles]
    lows = [c.get('low', c.get('l', 0)) for c in prev_candles]

    resistance = max(highs)
    support = min(lows)

    c_open = last_candle.get('open', last_candle.get('o', 0))
    c_close = last_candle.get('close', last_candle.get('c', 0))
    c_high = last_candle.get('high', last_candle.get('h', 0))
    c_low = last_candle.get('low', last_candle.get('l', 0))

    body_size = abs(c_close - c_open)
    upper_wick = c_high - max(c_open, c_close)
    lower_wick = min(c_open, c_close) - c_low

    # 1. Resistance Rejection / Bearish Reversal
    if c_high >= resistance and upper_wick > (body_size * 0.8) and c_close < c_open:
        return "PUT", "Strong Resistance Rejection + Upper Wick Pressure"

    # 2. Support Bounce / Bullish Reversal
    if c_low <= support and lower_wick > (body_size * 0.8) and c_close > c_open:
        return "CALL", "Key Support Bounce + Lower Wick Buying Pressure"

    # 3. 50% SNR Level Retracement
    snr_50 = support + (resistance - support) * 0.5
    if c_open > snr_50 and c_low <= snr_50 and c_close > snr_50 and lower_wick > 0:
        return "CALL", "50% SNR Retracement + Bullish Wick Rejection"
    elif c_open < snr_50 and c_high >= snr_50 and c_close < snr_50 and upper_wick > 0:
        return "PUT", "50% SNR Retracement + Bearish Wick Rejection"

    return None, None

def live_signal_engine():
    # Socket lock to avoid duplicate processes
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        lock_socket.bind(("127.0.0.1", 45454))
    except socket.error:
        logging.warning("Secondary process detected. Signal loop stopped.")
        return

    start_text = (
        "🚀 <b>TAMIL STAR OTC VIP LIVE PRICE ACTION ENGINE</b> 🚀\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <b>Mode:</b> Direct Quotex OTC Live Chart Stream\n"
        "📊 <b>Platform:</b> Quotex OTC (13 Assets)\n"
        "⏱ <b>Timeframe:</b> 1 MIN (M1 Candle)\n"
        "🎯 <b>Accuracy:</b> S&R + 50% SNR + Wick Rejections\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Scanning Quotex live market feeds for confirmed setups...</i>"
    )
    send_telegram_message(start_text)
    time.sleep(5)

    while True:
        try:
            now_utc = datetime.utcnow()
            now_ist = now_utc + timedelta(hours=5, minutes=30)
            seconds = now_ist.second

            # Scan and alert around :42 - :50 seconds before candle starts
            if 42 <= seconds <= 52:
                entry_time = (now_ist + timedelta(minutes=1)).replace(second=0, microsecond=0)
                time_str = entry_time.strftime("%H:%M")

                qc = get_quotex_client()
                selected_pair = None
                direction = None
                reason = None

                for pair_info in PAIRS:
                    try:
                        if qc and qc.check_connect():
                            candles = qc.get_candles(pair_info["asset"], 60, 20, time.time())
                        else:
                            candles = []
                    except Exception:
                        candles = []

                    dir_found, r_found = analyze_price_action(candles)
                    if dir_found:
                        selected_pair = pair_info
                        direction = dir_found
                        reason = r_found
                        break

                # If market setup is confirmed
                if selected_pair and direction:
                    if direction == "CALL":
                        banner = "🟩🟩🟩🟩🟩🟩🟩🟩\n⬆️⬆️ <b>CALL / UP (BUY)</b> ⬆️⬆️\n🟩🟩🟩🟩🟩🟩🟩🟩"
                        trade_name = "CALL 🟢 (BUY)"
                    else:
                        banner = "🟥🟥🟥🟥🟥🟥🟥🟥\n⬇️⬇️ <b>PUT / DOWN (SELL)</b> ⬇️⬇️\n🟥🟥🟥🟥🟥🟥🟥🟥"
                        trade_name = "PUT 🔴 (SELL)"

                    signal_msg = (
                        "🎯 <b>TAMIL STAR LIVE SURE-SHOT</b> 🎯\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 <b>Asset:</b> <code>{selected_pair['display']}</code>\n"
                        f"⏰ <b>Entry Time:</b> <b>{time_str} IST</b>\n"
                        f"⏱ <b>Expiry:</b> 1 MIN (M1 Candle)\n\n"
                        f"{banner}\n\n"
                        f"💡 <b>Setup:</b> <i>{reason}</i>\n"
                        "🛡 <b>Safety:</b> 1-Step MTG Applicable\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "⚡ <i>Take trade at :00 second candle open!</i>"
                    )
                    send_telegram_message(signal_msg)

                    # Wait until candle closes (Entry + 62 seconds)
                    wait_seconds = (60 - seconds) + 62
                    time.sleep(wait_seconds)

                    # Verify Real Trade Result from Live Price
                    win_status = False
                    try:
                        if qc and qc.check_connect():
                            res_candles = qc.get_candles(selected_pair["asset"], 60, 2, time.time())
                            if res_candles and len(res_candles) >= 1:
                                target_c = res_candles[-1]
                                o_p = target_c.get('open', target_c.get('o', 0))
                                c_p = target_c.get('close', target_c.get('c', 0))
                                if direction == "CALL" and c_p > o_p:
                                    win_status = True
                                elif direction == "PUT" and c_p < o_p:
                                    win_status = True
                    except Exception as e:
                        logging.error(f"Error checking real result: {e}")

                    if win_status:
                        result_msg = (
                            "✅ <b>TRADE RESULT: DIRECT SURE-SHOT!</b> ✅\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"📊 <b>Asset:</b> {selected_pair['display']}\n"
                            f"📈 <b>Signal:</b> {trade_name}\n"
                            "🏆 <b>Status:</b> <b>DIRECT WIN 🟢🔥</b>\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            "🎯 <i>Clean Breakout Win! Next asset scanning...</i>"
                        )
                        send_telegram_message(result_msg)
                    else:
                        # 1-Step MTG Alert
                        mtg_banner = (
                            "⚠️ <b>1-STEP MARTINGALE (MTG LEVEL 1)!</b> ⚠️\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"📊 <b>Asset:</b> <code>{selected_pair['display']}</code>\n"
                            f"⚡ Continue Same Direction:\n\n{banner}\n\n"
                            "⏱ <b>Expiry:</b> Next 1 MIN Candle\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━"
                        )
                        send_telegram_message(mtg_banner)
                        time.sleep(63)

                        # Check MTG Real Result
                        mtg_win = False
                        try:
                            if qc and qc.check_connect():
                                mtg_candles = qc.get_candles(selected_pair["asset"], 60, 2, time.time())
                                if mtg_candles and len(mtg_candles) >= 1:
                                    mc = mtg_candles[-1]
                                    mo = mc.get('open', mc.get('o', 0))
                                    mc_p = mc.get('close', mc.get('c', 0))
                                    if direction == "CALL" and mc_p > mo:
                                        mtg_win = True
                                    elif direction == "PUT" and mc_p < mo:
                                        mtg_win = True
                        except Exception:
                            pass

                        if mtg_win:
                            res_text = (
                                "✅ <b>TRADE RESULT: MTG WIN!</b> ✅\n"
                                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"📊 <b>Asset:</b> {selected_pair['display']}\n"
                                "🏆 <b>Status:</b> <b>1-STEP MTG WIN 🟢👍</b>\n"
                                "━━━━━━━━━━━━━━━━━━━━━━━━"
                            )
                        else:
                            res_text = (
                                "❌ <b>TRADE RESULT: LOSS</b> ❌\n"
                                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"📊 <b>Asset:</b> {selected_pair['display']}\n"
                                "⚠️ <b>Status:</b> <b>LOSS 🔴</b>\n"
                                "━━━━━━━━━━━━━━━━━━━━━━━━"
                            )
                        send_telegram_message(res_text)

                    # 2 நிமிட இடைவெளி
                    time.sleep(120)
                else:
                    time.sleep(1)
            else:
                time.sleep(1)

        except Exception as e:
            logging.error(f"Signal loop error: {e}")
            time.sleep(5)

# Start engine background thread
t = threading.Thread(target=live_signal_engine, daemon=True)
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
  
