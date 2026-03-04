# Stock Signal Bot — Agent Context

## Project Purpose
A GitHub Actions-based stock signal scanner. It fetches daily OHLCV data, runs configurable trade strategies per stock, and sends Telegram notifications when signals are triggered. The user manually decides whether to act on signals.

## Tech Stack
- **Python 3.11**
- **yfinance** — market data fetching (supports US stocks, ETFs, and TSX tickers like `VDY.TO`)
- **pandas** — data manipulation and MA calculations
- **requests** — Telegram Bot API calls
- **pyyaml** — watchlist config parsing
- **GitHub Actions** — scheduler (runs Mon–Fri after market close)

## Quick

- setup environment
```
source .venv/bin/activate
```

- run
```
cd src
python main.py
```

## Project Structure
```
stock-signal-bot/
├── .github/
│   └── workflows/
│       └── daily_scan.yml       # Cron: 21:30 UTC Mon–Fri (4:30 PM EST)
├── config/
│   └── watchlist.yml            # Per-stock strategy configuration
├── src/
│   ├── main.py                  # Entrypoint: fetch → scan → notify
│   ├── fetch_data.py            # Downloads 100 days OHLCV, saves to data/*.csv
│   ├── notify.py                # Telegram sender (send_summary, send_error_alert)
│   └── strategies/
│       ├── __init__.py
│       └── ma_crossover.py      # Golden Cross / Death Cross detection
├── data/                        # Auto-generated CSVs (gitignored)
├── requirements.txt
└── README.md
```

## Current Watchlist
| Ticker | Name | Exchange |
|--------|------|----------|
| AAPL | Apple Inc. | NASDAQ |
| NVDA | NVIDIA Corporation | NASDAQ |
| TSLA | Tesla Inc. | NASDAQ |
| MSFT | Microsoft Corporation | NASDAQ |
| PPLT | Aberdeen Physical Platinum ETF | NYSE |
| SPY | SPDR S&P 500 ETF | NYSE |
| VDY.TO | Vanguard FTSE Canadian High Dividend ETF | TSX |

## Active Strategies
### MA Crossover (`src/strategies/ma_crossover.py`)
- **BUY (Golden Cross):** fast MA crosses above slow MA
- **SELL (Death Cross):** fast MA crosses below slow MA
- Returns a `Signal` dataclass or `None`
- Configurable `fast_period` and `slow_period` per stock in `watchlist.yml`

## Signal Dataclass
```python
@dataclass
class Signal:
    ticker: str
    signal_type: str      # "BUY" or "SELL"
    strategy: str         # e.g. "ma_crossover"
    price: float
    fast_ma: float
    slow_ma: float
    fast_period: int
    slow_period: int
    date: str
    message: str          # Pre-formatted Telegram message
```

## Adding a New Strategy
1. Create `src/strategies/<strategy_name>.py`
2. Implement `run(ticker: str, df: pd.DataFrame, **kwargs) -> Optional[Signal]`
3. Add the strategy key under the stock in `config/watchlist.yml`
4. Wire it up in `src/main.py` alongside the existing `ma_crossover` block

Example `watchlist.yml` strategy config:
```yaml
AAPL:
  enabled: true
  strategies:
    ma_crossover:
      enabled: true
      fast_period: 5
      slow_period: 20
    rsi:                  # future strategy example
      enabled: true
      period: 14
      oversold: 30
      overbought: 70
```

## Notification Flow
- `notify.send_summary(signals, scanned_count)` — always called; sends "no signals" message if list is empty
- `notify.send_error_alert(error_msg)` — called in main.py exception handler
- Telegram uses `parse_mode: Markdown` — use `*bold*` and `_italic_` in messages

## GitHub Secrets Required
| Secret | Description |
|--------|-------------|
| `TELEGRAM_BOT_TOKEN` | From @BotFather |
| `TELEGRAM_CHAT_ID` | Your personal Telegram chat ID |

## Data Flow
```
GitHub Actions (cron)
  → main.py
    → fetch_data.py        # yfinance → data/<TICKER>.csv
    → strategies/*.py      # loads CSV, returns Signal or None
    → notify.py            # POSTs to Telegram Bot API
```

## Known Constraints
- `data/` directory is gitignored — data is re-fetched fresh on every run
- yfinance rate limits: avoid fetching more than ~20 tickers per run without adding delays
- TSX tickers require `.TO` suffix (e.g. `VDY.TO`) — already handled in watchlist
- Telegram messages are truncated to 1000 chars in error alerts to stay within API limits

## Potential Next Features
- RSI strategy (`strategies/rsi.py`)
- Bollinger Bands strategy (`strategies/bollinger.py`)
- Volume spike detection (`strategies/volume_spike.py`)
- Signal history log (append to `data/signals_log.csv`)
- Weekly summary report
- Per-stock price alerts (e.g. "notify me if AAPL drops below $180")
