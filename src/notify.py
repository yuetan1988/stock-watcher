"""
notify.py
Sends trade signals to Telegram via Bot API.

Required GitHub Secrets:
  TELEGRAM_BOT_TOKEN  — from @BotFather
  TELEGRAM_CHAT_ID    — your personal chat ID (get from @userinfobot)
"""

import os
import requests
from typing import List


TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram(message: str) -> bool:
    """Send a message via Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"  Telegram sent OK: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  ERROR sending Telegram: {e}")
        return False


def send_summary(signals: list, scanned_count: int):
    """
    Send a daily scan summary message.
    Always sends even if no signals, so you know the bot ran.
    """
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")

    if signals:
        header = f"📊 *Daily Scan — {today}*\n{len(signals)} signal(s) found:\n\n"
        body = "\n---\n".join([s.message for s in signals])
        msg = header + body
    else:
        msg = (
            f"📊 *Daily Scan — {today}*\n"
            f"No signals today. Scanned {scanned_count} stock(s).\n"
            f"_Monitoring: MA Crossover strategy_"
        )

    send_telegram(msg)


def send_error_alert(error_msg: str):
    """Send an error notification so you know something went wrong."""
    msg = f"⚠️ *Stock Bot Error*\n```\n{error_msg}\n```"
    send_telegram(msg)