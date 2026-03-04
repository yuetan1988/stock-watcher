"""
fetch_data.py
Fetches daily OHLCV data for all stocks in the watchlist using yfinance.
Saves data to data/ directory as CSV files.
"""

import os
import yaml
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path("data")
CONFIG_PATH = Path("config/watchlist.yml")


def load_watchlist():
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    return config.get("stocks", {})


def fetch_stock_data(ticker: str, period_days: int = 100) -> pd.DataFrame:
    """
    Fetch recent OHLCV data for a given ticker.
    We fetch 100 days by default to have enough history for MA calculations.
    Uses relative time period to avoid issues with incorrect system dates.
    """
    print(f"  Fetching {ticker} (last {period_days} days)...")

    stock = yf.Ticker(ticker)
    df = stock.history(period=f"{period_days}d")

    if df.empty:
        print(f"  WARNING: No data returned for {ticker}")
        return None

    df.index = df.index.tz_localize(None)  # Remove timezone for clean CSV
    df = df[["Open", "High", "Low", "Close", "Volume"]]
    df.index.name = "Date"
    return df


def save_stock_data(ticker: str, df: pd.DataFrame):
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / f"{ticker}.csv"
    df.to_csv(path)
    print(f"  Saved {len(df)} rows to {path}")


def load_stock_data(ticker: str) -> pd.DataFrame:
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