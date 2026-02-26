# 📈 Stock Signal Bot

A GitHub Actions bot that scans your watchlist daily, detects trade signals, and sends you a Telegram message. You decide when to buy or sell.

---

## 🗂 Project Structure

```
stock-signal-bot/
├── .github/
│   └── workflows/
│       └── daily_scan.yml      # Runs Mon–Fri after market close
├── config/
│   └── watchlist.yml           # Your stocks + strategy settings
├── src/
│   ├── main.py                 # Entrypoint: fetch → scan → notify
│   ├── fetch_data.py           # Downloads OHLCV data via yfinance
│   ├── notify.py               # Telegram notification sender
│   └── strategies/
│       ├── __init__.py
│       └── ma_crossover.py     # MA Crossover strategy
├── requirements.txt
└── README.md
```

---

## 🚀 Setup Guide

### Step 1 — Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **Bot Token** (looks like `123456789:ABCdef...`)
4. Start a chat with your new bot (send it any message)
5. Get your **Chat ID**: visit this URL in your browser:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   Look for `"id"` inside `"chat"` — that's your Chat ID

### Step 2 — Add GitHub Secrets

In your GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Your bot token from BotFather |
| `TELEGRAM_CHAT_ID` | Your personal Telegram chat ID |

### Step 3 — Configure Your Watchlist

Edit `config/watchlist.yml` to add your stocks and customize strategies:

```yaml
stocks:
  AAPL:
    name: "Apple Inc."
    enabled: true
    strategies:
      ma_crossover:
        enabled: true
        fast_period: 5    # 5-day MA
        slow_period: 20   # 20-day MA
```

### Step 4 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial stock signal bot"
git remote add origin https://github.com/YOUR_USERNAME/stock-signal-bot.git
git push -u origin main
```

The bot will now run automatically every weekday at 4:30 PM EST (after market close).

---

## ⏱ Schedule

The workflow runs at `21:30 UTC` (Mon–Fri) = **4:30 PM Eastern Time**.

To change the time, edit `.github/workflows/daily_scan.yml`:
```yaml
- cron: "30 21 * * 1-5"
```

Use [crontab.guru](https://crontab.guru) to build your preferred schedule.

---

## 📬 Telegram Message Examples

**When a signal fires:**
```
📊 Daily Scan — 2025-03-15
1 signal(s) found:

🟢 BUY Signal — AAPL
Strategy: MA Crossover (MA5 / MA20)
Date: 2025-03-15
Price: $198.45
MA5: $196.30  ↑ crossed above
MA20: $193.10
```

**When no signals:**
```
📊 Daily Scan — 2025-03-15
No signals today. Scanned 4 stock(s).
Monitoring: MA Crossover strategy
```

---

## 🧪 Manual Test

To run locally and test:

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
python src/main.py
```

You can also trigger a manual run in GitHub:
**Actions tab → Daily Stock Signal Scanner → Run workflow**

---

## 📐 Strategy: MA Crossover

| Signal | Condition |
|--------|-----------|
| 🟢 BUY | Fast MA crosses **above** Slow MA (Golden Cross) |
| 🔴 SELL | Fast MA crosses **below** Slow MA (Death Cross) |

### Recommended Settings by Style

| Style | Fast MA | Slow MA |
|-------|---------|---------|
| Short-term swing | 5 | 20 |
| Medium-term | 10 | 30 |
| Long-term trend | 50 | 200 |

---

## ➕ Adding More Strategies

Add a new file to `src/strategies/`, e.g. `rsi.py`, with a `run(ticker, df, **kwargs)` function that returns a `Signal` or `None`. Then reference it in `config/watchlist.yml` and `src/main.py`.

---

## ⚠️ Disclaimer

This bot is for informational purposes only. It does not constitute financial advice. All trades are your own decision.
