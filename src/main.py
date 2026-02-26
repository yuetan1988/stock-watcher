"""
main.py
Main entrypoint: fetch data → run strategies → send notifications.
"""

import sys
import traceback
from pathlib import Path

# Make sure src/ is in path
sys.path.insert(0, str(Path(__file__).parent))

import yaml
from fetch_data import load_watchlist, fetch_stock_data, save_stock_data, load_stock_data
from strategies import ma_crossover
from notify import send_summary, send_error_alert


CONFIG_PATH = Path("config/watchlist.yml")


def run_scan():
    print("\n========== Stock Signal Scanner ==========")

    # 1. Load watchlist
    stocks = load_watchlist()
    enabled_stocks = {k: v for k, v in stocks.items() if v.get("enabled", True)}
    print(f"Watching {len(enabled_stocks)} stocks: {list(enabled_stocks.keys())}\n")

    # 2. Fetch latest data for all stocks
    print("--- Step 1: Fetching Data ---")
    for ticker in enabled_stocks:
        try:
            df = fetch_stock_data(ticker)
            if df is not None:
                save_stock_data(ticker, df)
        except Exception as e:
            print(f"  ERROR fetching {ticker}: {e}")

    # 3. Run strategies and collect signals
    print("\n--- Step 2: Running Strategies ---")
    all_signals = []

    for ticker, cfg in enabled_stocks.items():
        strategies = cfg.get("strategies", {})

        # --- MA Crossover ---
        ma_cfg = strategies.get("ma_crossover", {})
        if ma_cfg.get("enabled", False):
            fast = ma_cfg.get("fast_period", 5)
            slow = ma_cfg.get("slow_period", 20)
            df = load_stock_data(ticker)
            signal = ma_crossover.run(ticker, df, fast_period=fast, slow_period=slow)
            if signal:
                print(f"  *** SIGNAL: {signal.signal_type} {ticker} via {signal.strategy} ***")
                all_signals.append(signal)

    # 4. Send notifications
    print("\n--- Step 3: Sending Notifications ---")
    send_summary(all_signals, scanned_count=len(enabled_stocks))

    print("\n========== Scan Complete ==========")
    print(f"Signals fired: {len(all_signals)}")
    for s in all_signals:
        print(f"  {s.signal_type} {s.ticker} @ ${s.price:.2f}")


if __name__ == "__main__":
    try:
        run_scan()
    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"FATAL ERROR:\n{error_detail}")
        send_error_alert(error_detail[:1000])  # Truncate for Telegram
        sys.exit(1)