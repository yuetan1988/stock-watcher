"""
strategies/ma_crossover.py

Moving Average Crossover Strategy.
Generates a BUY signal when the fast MA crosses ABOVE the slow MA,
and a SELL signal when the fast MA crosses BELOW the slow MA.
"""

import pandas as pd
from dataclasses import dataclass
from typing import Optional


@dataclass
class Signal:
    ticker: str
    signal_type: str        # "BUY" or "SELL"
    strategy: str
    price: float
    prev_price: float
    price_change_pct: float
    fast_ma: float
    slow_ma: float
    fast_period: int
    slow_period: int
    date: str
    message: str


def run(ticker: str, df: pd.DataFrame, fast_period: int = 5, slow_period: int = 20) -> Optional[Signal]:
    """
    Check for MA crossover signal on the latest data.

    Returns a Signal object if a crossover occurred today, else None.
    """
    if df is None or len(df) < slow_period + 2:
        print(f"  [{ticker}] Not enough data for MA({fast_period}/{slow_period})")
        return None

    df = df.copy()
    df[f"MA{fast_period}"] = df["Close"].rolling(window=fast_period).mean()
    df[f"MA{slow_period}"] = df["Close"].rolling(window=slow_period).mean()

    # Drop rows where MAs are not yet calculated
    df = df.dropna(subset=[f"MA{fast_period}", f"MA{slow_period}"])

    if len(df) < 2:
        return None

    # Today's and yesterday's values
    today = df.iloc[-1]
    yesterday = df.iloc[-2]

    fast_today = today[f"MA{fast_period}"]
    slow_today = today[f"MA{slow_period}"]
    fast_yesterday = yesterday[f"MA{fast_period}"]
    slow_yesterday = yesterday[f"MA{slow_period}"]

    current_price = today["Close"]
    prev_price = yesterday["Close"]
    price_change_pct = ((current_price - prev_price) / prev_price) * 100
    date_str = str(today.name.date()) if hasattr(today.name, 'date') else str(today.name)

    # Detect crossover
    golden_cross = (fast_yesterday < slow_yesterday) and (fast_today > slow_today)
    death_cross = (fast_yesterday > slow_yesterday) and (fast_today < slow_today)

    if golden_cross:
        msg = (
            f"📈 *MARKET SUMMARY* — {ticker}\n"
            f"Current Price: ${current_price:.2f}\n"
            f"Previous Price: ${prev_price:.2f}\n"
            f"Change: *{price_change_pct:+.2f}%*\n\n"
            f"🟢 *SUGGESTION: BUY* — {ticker}\n"
            f"Strategy: MA Crossover (MA{fast_period} / MA{slow_period})\n"
            f"Date: {date_str}\n"
            f"Price: ${current_price:.2f}\n"
            f"MA{fast_period}: ${fast_today:.2f}  ↑ crossed above\n"
            f"MA{slow_period}: ${slow_today:.2f}\n"
        )
        return Signal(ticker, "BUY", "ma_crossover", current_price, prev_price, price_change_pct,
                      fast_today, slow_today, fast_period, slow_period, date_str, msg)

    elif death_cross:
        msg = (
            f"📈 *MARKET SUMMARY* — {ticker}\n"
            f"Current Price: ${current_price:.2f}\n"
            f"Previous Price: ${prev_price:.2f}\n"
            f"Change: *{price_change_pct:+.2f}%*\n\n"
            f"🔴 *SUGGESTION: SELL* — {ticker}\n"
            f"Strategy: MA Crossover (MA{fast_period} / MA{slow_period})\n"
            f"Date: {date_str}\n"
            f"Price: ${current_price:.2f}\n"
            f"MA{fast_period}: ${fast_today:.2f}  ↓ crossed below\n"
            f"MA{slow_period}: ${slow_today:.2f}\n"
        )
        return Signal(ticker, "SELL", "ma_crossover", current_price, prev_price, price_change_pct,
                      fast_today, slow_today, fast_period, slow_period, date_str, msg)

    else:
        # No crossover, but log current state with price info
        direction = "above" if fast_today > slow_today else "below"
        price_change_pct = ((current_price - prev_price) / prev_price) * 100
        print(f"  [{ticker}] No signal. Price: ${current_price:.2f} ({price_change_pct:+.2f}%), MA{fast_period}={fast_today:.2f} is {direction} MA{slow_period}={slow_today:.2f}")
        return None