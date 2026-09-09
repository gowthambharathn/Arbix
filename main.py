"""
ArbiX Arbitrage Bot Main Runner
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Dict, Tuple

# Ensure current project directory is in Python module search path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import config.settings as settings
from arbitrage.finder import find_arbitrage_opportunities
from market_data.streamer import MarketDataStreamer

# Setup clean logger formatting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("ArbiX.Main")

# Fallback attribute resolution for settings variables
EXCHANGES = getattr(settings, "DEFAULT_EXCHANGES", getattr(settings, "EXCHANGES", ["binance", "kraken", "bybit"]))
SYMBOLS = getattr(settings, "DEFAULT_SYMBOLS", getattr(settings, "TRADING_SYMBOLS", getattr(settings, "SYMBOLS", ["BTC/USDT", "SOL/USDT", "DOGE/USDT", "PEPE/USDT"])))
MIN_PROFIT_PERCENTAGE = getattr(settings, "MIN_PROFIT_PERCENTAGE", 0.20)


def print_dashboard(
    order_books: Dict[Tuple[str, str], object],
    symbols: list[str],
    exchanges: list[str],
    opportunities: list,
) -> None:
    """Print a clean live dashboard to the terminal."""
    total_books = len(order_books)
    max_possible = len(symbols) * len(exchanges)

    print("\n" + "=" * 70)
    print(f" 🚀 ARBIX LIVE MONITORING | Active Streams: {total_books}/{max_possible}")
    print("=" * 70)
    print(f"{'SYMBOL':<10} | {'BUY AT':<8} | {'SELL AT':<8} | {'BEST SPREAD':<12} | {'NET PROFIT':<10}")
    print("-" * 70)

    for symbol in symbols:
        symbol_opps = [o for o in opportunities if o.symbol == symbol]
        if not symbol_opps:
            print(f"{symbol:<10} | {'N/A':<8} | {'N/A':<8} | {'Waiting data':<12} | {'N/A':<10}")
            continue

        best_opp = max(symbol_opps, key=lambda x: x.gross_spread_pct)
        status_flag = "🔥 YES" if getattr(best_opp, "is_profitable", False) else f"{best_opp.net_spread_pct:+.3f}%"

        print(
            f"{symbol:<10} | {best_opp.buy_exchange:<8} | {best_opp.sell_exchange:<8} | "
            f"{best_opp.gross_spread_pct:+.3f}%       | {status_flag:<10}"
        )

    print("=" * 70)
    print(f"Target Profit Threshold: >={MIN_PROFIT_PERCENTAGE}% (Listening for opportunities...)\n")


async def main() -> None:
    logger.info(f"Initializing ArbiX Bot | Symbols: {SYMBOLS} | Exchanges: {EXCHANGES}")

    streamer = MarketDataStreamer(exchanges=EXCHANGES, symbols=SYMBOLS)

    tasks = []
    for ex_name in EXCHANGES:
        for symbol in SYMBOLS:
            task = asyncio.create_task(
                streamer.watch_exchange_symbol_order_book(ex_name, symbol)
            )
            tasks.append(task)

    logger.info("Starting market streams and scanning loop...")

    try:
        while True:
            await asyncio.sleep(4)

            opportunities = find_arbitrage_opportunities(
                order_books=streamer.order_books,
                symbols=SYMBOLS,
                exchanges=EXCHANGES,
            )

            print_dashboard(
                order_books=streamer.order_books,
                symbols=SYMBOLS,
                exchanges=EXCHANGES,
                opportunities=opportunities,
            )

    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Stopping bot and closing exchange streams...")
    finally:
        for task in tasks:
            task.cancel()
        await streamer.close_all()
        logger.info("ArbiX Bot stopped cleanly.")


if __name__ == "__main__":
    asyncio.run(main())