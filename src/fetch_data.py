"""
fetch_data.py
Fetches daily OHLCV data for all stocks in the watchlist using yfinance.
Saves data to data/ directory as CSV files.
"""

import os
import time
from typing import Optional
import yaml
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import random
import requests

DATA_DIR = Path("data")
CONFIG_PATH = Path("config/watchlist.yml")

# Create a session with proper headers to avoid being blocked
session = requests.Session()
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
]
session.headers.update({
    "User-Agent": random.choice(user_agents),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
})


def load_watchlist():
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    return config.get("stocks", {})


def fetch_stock_data(ticker: str, period_days: int = 100, max_retries: int = 3) -> Optional[pd.DataFrame]:
    """
    Fetch recent OHLCV data for a given ticker.
    We fetch 100 days by default to have enough history for MA calculations.
    Uses relative time period to avoid issues with incorrect system dates.
    Includes retry logic with exponential backoff to handle rate limiting.
    Uses yfinance.download with proper headers to avoid being blocked.
    """
    print(f"  Fetching {ticker} (last {period_days} days)...")

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                sleep_time = (5 * attempt) + random.uniform(2, 5)  # 5+ seconds, increasing
                print(f"    Retry attempt {attempt + 1}/{max_retries} after {sleep_time:.1f}s delay")
                time.sleep(sleep_time)
            
            # Use yfinance.download which is more reliable for single tickers
            # Add a baseline delay even on first attempt to avoid rate limiting
            if attempt == 0:
                time.sleep(random.uniform(3, 6))
                
            df = yf.download(
                tickers=ticker,
                period=f"{period_days}d",
                progress=False,
                timeout=60,
                session=session,
            )

            if df is None or (hasattr(df, 'empty') and df.empty) or (hasattr(df, 'shape') and df.shape[0] == 0):
                print(f"  WARNING: No data returned for {ticker}")
                if attempt < max_retries - 1:
                    continue
                return None

            # yfinance download returns a MultiIndex DataFrame for single tickers
            # We need to flatten it when there's a single ticker
            if hasattr(df, 'columns') and isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)

            if hasattr(df, 'index') and hasattr(df.index, 'tz_localize'):
                df.index = df.index.tz_localize(None)  # Remove timezone for clean CSV
            
            if hasattr(df, '__getitem__'):
                df = df[["Open", "High", "Low", "Close", "Volume"]]
            
            if hasattr(df, 'index'):
                df.index.name = "Date"
            
            return df
            
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                continue
            print(f"  ERROR: Failed to fetch {ticker} after {max_retries} attempts")
            return None
    
    time.sleep(random.uniform(1, 2))  # Add delay between ticker fetches
    return None


def save_stock_data(ticker: str, df: pd.DataFrame):
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / f"{ticker}.csv"
    df.to_csv(path)
    print(f"  Saved {len(df)} rows to {path}")


def load_stock_data(ticker: str) -> Optional[pd.DataFrame]:
    """Load saved CSV data for a ticker."""
    path = DATA_DIR / f"{ticker}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, index_col="Date", parse_dates=True)
    return df


def run():
    print("=== Fetching stock data ===")
    stocks = load_watchlist()

    success, failed = [], []
    for ticker, cfg in stocks.items():
        if not cfg.get("enabled", True):
            print(f"  Skipping {ticker} (disabled)")
            continue
        try:
            df = fetch_stock_data(ticker)
            if df is not None:
                save_stock_data(ticker, df)
                success.append(ticker)
            else:
                failed.append(ticker)
        except Exception as e:
            print(f"  ERROR fetching {ticker}: {e}")
            failed.append(ticker)

    print(f"\nDone. Success: {success} | Failed: {failed}")
    return failed  # Return failures so caller can handle


if __name__ == "__main__":
    run()