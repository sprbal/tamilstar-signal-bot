"""
main.py
Research / Paper Alert Telegram Bot

IMPORTANT:
- RESEARCH / PAPER TRADING ONLY.
- Does NOT place trades.
- Does NOT provide Martingale/MTG instructions.
- Signals are experimental technical-analysis alerts and are not
  financial advice or guarantees of accuracy.
- Set TELEGRAM_BOT_TOKEN in the environment.
- Never hard-code your Telegram bot token.

Designed for:
    Render Web Service
    Flask keep-alive server on 0.0.0.0:8080

Python:
    3.10+

Environment variables:
    TELEGRAM_BOT_TOKEN=your_new_bot_token
    MARKET_DATA_URL=optional REST endpoint
    SCAN_SECONDS=5
"""

from __future__ import annotations

import io
import json
import logging
import math
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import requests
import pandas as pd
import numpy as np

from flask import Flask, jsonify
from PIL import Image, ImageDraw, ImageFont


# ============================================================================
# CONFIGURATION
# ============================================================================

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

PORT = int(os.getenv("PORT", "8080"))
SCAN_SECONDS = int(os.getenv("SCAN_SECONDS", "5"))

TELEGRAM_API = (
    f"https://api.telegram.org/bot{BOT_TOKEN}"
    if BOT_TOKEN
    else ""
)

# Research instruments.
ASSETS = [
    "USD/INR (OTC)",
    "USD/BDT (OTC)",
    "USD/PKR (OTC)",
    "USD/BRL (OTC)",
    "USD/MXN (OTC)",
    "USD/COP (OTC)",
    "USD/PHP (OTC)",
    "USD/IDR (OTC)",
    "USD/DZD (OTC)",
    "USD/ARS (OTC)",
    "USD/ZAR (OTC)",
    "USD/NGN (OTC)",
    "USD/EGP (OTC)",
]

# Prevent multiple paper alerts in the same minute.
SIGNAL_COOLDOWN_SECONDS = 180

# Telegram polling.
UPDATE_TIMEOUT = 20

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

log = logging.getLogger("research-alert-bot")


# ============================================================================
# FLASK KEEP-ALIVE
# ============================================================================

app = Flask(__name__)


@app.get("/")
def index():
    return jsonify(
        {
            "status": "online",
            "mode": "RESEARCH / PAPER ONLY",
            "service": "telegram-research-alert-bot",
        }
    )


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "healthy",
            "mode": "research",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


def start_keep_alive() -> None:
    """
    Start Flask in a background thread so the market-analysis loop
    can run independently.
    """
    thread = threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0",
            port=PORT,
            debug=False,
            use_reloader=False,
        ),
        daemon=True,
    )

    thread.start()
    log.info("Flask keep-alive started on 0.0.0.0:%s", PORT)


# ============================================================================
# TELEGRAM
# ============================================================================

class TelegramClient:
    def __init__(self, token: str):
        if not token:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN environment variable is missing."
            )

        self.base_url = f"https://api.telegram.org/bot{token}"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "ResearchTelegramBot/1.0",
            }
        )

        self.chat_id: Optional[int] = None
        self.offset: Optional[int] = None

    def call(
        self,
        method: str,
        payload: Optional[dict[str, Any]] = None,
        timeout: int = 30,
    ) -> dict[str, Any]:

        url = f"{self.base_url}/{method}"

        response = self.session.post(
            url,
            json=payload or {},
            timeout=timeout,
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("ok"):
            raise RuntimeError(
                f"Telegram API error: {data}"
            )

        return data

    def discover_chat_id(self) -> Optional[int]:
        """
        Discover a Telegram destination automatically.

        Handles:
            channel_post
            my_chat_member
            message

        The first suitable channel/group/chat discovered is retained.
        """

        log.info("Attempting automatic Telegram destination discovery...")

        try:
            result = self.call(
                "getUpdates",
                {
                    "timeout": 0,
                    "allowed_updates": [
                        "message",
                        "channel_post",
                        "my_chat_member",
                    ],
                },
            )
        except Exception as exc:
            log.error(
                "Unable to retrieve Telegram updates: %s",
                exc,
            )
            return None

        updates = result.get("result", [])

        if not updates:
            log.warning(
                "No Telegram updates available. "
                "Send a message to the bot or add it to the channel/group."
            )
            return None

        for update in updates:
            self.offset = update.get("update_id", 0) + 1

            # --------------------------------------------------------------
            # channel_post
            # --------------------------------------------------------------

            channel_post = update.get("channel_post")

            if channel_post:
                chat = channel_post.get("chat", {})
                chat_id = chat.get("id")

                if chat_id is not None:
                    self.chat_id = int(chat_id)

                    log.info(
                        "Discovered channel through channel_post: %s",
                        self.chat_id,
                    )

                    return self.chat_id

            # --------------------------------------------------------------
            # my_chat_member
            # --------------------------------------------------------------

            member_update = update.get("my_chat_member")

            if member_update:
                chat = member_update.get("chat", {})
                chat_type = chat.get("type")

                if chat_type in {
                    "channel",
                    "group",
                    "supergroup",
                }:
                    chat_id = chat.get("id")

                    if chat_id is not None:
                        self.chat_id = int(chat_id)

                        log.info(
                            "Discovered destination through "
                            "my_chat_member: %s",
                            self.chat_id,
                        )

                        return self.chat_id

            # --------------------------------------------------------------
            # message
            # --------------------------------------------------------------

            message = update.get("message")

            if message:
                chat = message.get("chat", {})
                chat_type = chat.get("type")

                if chat_type in {
                    "private",
                    "group",
                    "supergroup",
                    "channel",
                }:
                    chat_id = chat.get("id")

                    if chat_id is not None:
                        self.chat_id = int(chat_id)

                        log.info(
                            "Discovered destination through message: %s",
                            self.chat_id,
                        )

                        return self.chat_id

        return None

    def ensure_chat_id(self) -> bool:
        if self.chat_id is not None:
            return True

        return self.discover_chat_id() is not None

    def send_photo(
        self,
        image_bytes: bytes,
        caption: str,
    ) -> bool:

        if not self.ensure_chat_id():
            log.warning(
                "Telegram destination has not been discovered yet."
            )
            return False

        try:
            response = self.session.post(
                f"{self.base_url}/sendPhoto",
                data={
                    "chat_id": str(self.chat_id),
                    "caption": caption,
                    "parse_mode": "HTML",
                },
                files={
                    "photo": (
                        "research_signal.png",
                        image_bytes,
                        "image/png",
                    )
                },
                timeout=30,
            )

            response.raise_for_status()

            data = response.json()

            if not data.get("ok"):
                log.error("sendPhoto failed: %s", data)
                return False

            return True

        except Exception as exc:
            log.error(
                "Telegram sendPhoto error: %s",
                exc,
            )
            return False


# ============================================================================
# DATA MODEL
# ============================================================================

@dataclass
class Signal:
    asset: str
    direction: str
    candle_time: datetime
    entry_time: datetime
    price: float
    rsi: float
    ema9: float
    ema21: float
    ema50: float
    reason: str


# ============================================================================
# MARKET DATA
# ============================================================================

class MarketDataProvider:
    """
    Abstract market-data interface.

    The requested OTC instruments generally require a broker-specific
    feed. This class intentionally does not pretend that a generic public
    FX API is equivalent to Quotex OTC pricing.

    To connect a legitimate research feed, implement get_candles() so it
    returns:

        timestamp
        open
        high
        low
        close

    with one-minute OHLC candles.
    """

    def get_candles(
        self,
        asset: str,
        limit: int = 150,
    ) -> Optional[pd.DataFrame]:

        # No fabricated market prices.
        #
        # Returning None is preferable to generating fake signals.
        return None


# ============================================================================
# TECHNICAL INDICATORS
# ============================================================================

def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(
        span=period,
        adjust=False,
        min_periods=period,
    ).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    value = 100 - (100 / (1 + rs))

    return value.replace(
        [np.inf, -np.inf],
        np.nan,
    )


# ============================================================================
# MARKET STRUCTURE
# ============================================================================

def local_highs(
    highs: pd.Series,
    left: int = 2,
    right: int = 2,
) -> list[int]:

    result: list[int] = []

    for i in range(left, len(highs) - right):
        current = highs.iloc[i]

        left_values = highs.iloc[i - left:i]
        right_values = highs.iloc[i + 1:i + right + 1]

        if (
            current > left_values.max()
            and current >= right_values.max()
        ):
            result.append(i)

    return result


def local_lows(
    lows: pd.Series,
    left: int = 2,
    right: int = 2,
) -> list[int]:

    result: list[int] = []

    for i in range(left, len(lows) - right):
        current = lows.iloc[i]

        left_values = lows.iloc[i - left:i]
        right_values = lows.iloc[i + 1:i + right + 1]

        if (
            current < left_values.min()
            and current <= right_values.min()
        ):
            result.append(i)

    return result


def structure_bullish(df: pd.DataFrame) -> bool:
    """
    Research approximation of HH/HL structure.

    Requires:
        - at least two recent swing highs
        - at least two recent swing lows
        - recent highs increasing
        - recent lows increasing
    """

    highs = local_highs(df["high"])
    lows = local_lows(df["low"])

    if len(highs) < 2 or len(lows) < 2:
        return False

    h1, h2 = highs[-2:]
    l1, l2 = lows[-2:]

    return (
        df["high"].iloc[h2] > df["high"].iloc[h1]
        and df["low"].iloc[l2] > df["low"].iloc[l1]
    )


def structure_bearish(df: pd.DataFrame) -> bool:
    """
    Research approximation of LH/LL structure.
    """

    highs = local_highs(df["high"])
    lows = local_lows(df["low"])

    if len(highs) < 2 or len(lows) < 2:
        return False

    h1, h2 = highs[-2:]
    l1, l2 = lows[-2:]

    return (
        df["high"].iloc[h2] < df["high"].iloc[h1]
        and df["low"].iloc[l2] < df["low"].iloc[l1]
    )


# ============================================================================
# ROUND NUMBER FILTER
# ============================================================================

def nearest_round_level(price: float) -> float:
    """
    Generic 00 / 50-style research level.

    The actual pip/decimal convention differs between instruments,
    so this is deliberately treated as a normalized research filter
    rather than a broker-specific price rule.
    """

    if price <= 0:
        return price

    magnitude = 10 ** math.floor(math.log10(price))

    step = magnitude / 2

    return round(price / step) * step


def round_level_breakout(
    previous_close: float,
    current_close: float,
) -> bool:

    if previous_close <= 0 or current_close <= 0:
        return False

    level = nearest_round_level(previous_close)

    crossed_up = (
        previous_close < level
        and current_close >= level
    )

    crossed_down = (
        previous_close > level
        and current_close <= level
    )

    return crossed_up or crossed_down


# ============================================================================
# SIGNAL ENGINE
# ============================================================================

class ResearchSignalEngine:

    def evaluate(
        self,
        asset: str,
        candles: pd.DataFrame,
    ) -> Optional[Signal]:

        required = {
            "timestamp",
            "open",
            "high",
            "low",
            "close",
        }

        if not required.issubset(candles.columns):
            log.warning(
                "%s: missing required OHLC columns",
                asset,
            )
            return None

        if len(candles) < 60:
            return None

        df = candles.copy()

        # --------------------------------------------------------------
        # Normalize timestamps.
        # --------------------------------------------------------------

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            utc=True,
            errors="coerce",
        )

        df = df.dropna(
            subset=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
            ]
        )

        df = df.sort_values("timestamp")
        df = df.drop_duplicates("timestamp")

        if len(df) < 60:
            return None

        # --------------------------------------------------------------
        # Indicators.
        # --------------------------------------------------------------

        df["ema9"] = ema(df["close"], 9)
        df["ema21"] = ema(df["close"], 21)
        df["ema50"] = ema(df["close"], 50)
        df["rsi14"] = rsi(df["close"], 14)

        current = df.iloc[-1]
        previous = df.iloc[-2]

        if any(
            pd.isna(current[x])
            for x in [
                "ema9",
                "ema21",
                "ema50",
                "rsi14",
            ]
        ):
            return None

        close = float(current["close"])
        previous_close = float(previous["close"])

        high = float(current["high"])
        low = float(current["low"])
        open_price = float(current["open"])

        candle_range = high - low

        if candle_range <= 0:
            return None

        body = abs(close - open_price)

        body_ratio = body / candle_range

        # Strict candle-body filter.
        if body_ratio < 0.65:
            return None

        # --------------------------------------------------------------
        # Trend.
        # --------------------------------------------------------------

        uptrend = (
            current["ema9"]
            > current["ema21"]
            > current["ema50"]
            and close > current["ema9"]
        )

        downtrend = (
            current["ema9"]
            < current["ema21"]
            < current["ema50"]
            and close < current["ema9"]
        )

        # --------------------------------------------------------------
        # Round-number research confirmation.
        # --------------------------------------------------------------

        round_break = round_level_breakout(
            previous_close,
            close,
        )

        if not round_break:
            return None

        # --------------------------------------------------------------
        # Structure.
        # --------------------------------------------------------------

        bullish_structure = structure_bullish(df.iloc[:-1])
        bearish_structure = structure_bearish(df.iloc[:-1])

        current_rsi = float(current["rsi14"])

        # --------------------------------------------------------------
        # CALL.
        # --------------------------------------------------------------

        if (
            uptrend
            and bullish_structure
            and 54 <= current_rsi <= 75
            and close > open_price
        ):

            candle_time = current["timestamp"].to_pydatetime()

            entry_time = candle_time + timedelta(minutes=1)

            return Signal(
                asset=asset,
                direction="CALL",
                candle_time=candle_time,
                entry_time=entry_time,
                price=close,
                rsi=current_rsi,
                ema9=float(current["ema9"]),
                ema21=float(current["ema21"]),
                ema50=float(current["ema50"]),
                reason=(
                    "EMA trend alignment + bullish HH/HL structure + "
                    "body >= 65% + RSI range + round-level breakout"
                ),
            )

        # --------------------------------------------------------------
        # PUT.
        # --------------------------------------------------------------

        if (
            downtrend
            and bearish_structure
            and 25 <= current_rsi <= 46
            and close < open_price
        ):

            candle_time = current["timestamp"].to_pydatetime()

            entry_time = candle_time + timedelta(minutes=1)

            return Signal(
                asset=asset,
                direction="PUT",
          
