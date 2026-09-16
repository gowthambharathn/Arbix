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

from config.settings import settings
from arbitrage.finder import find_arbitrage_opportunities
from market_data.streamer import MarketDataStreamer


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("ArbiX.Main")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SYMBOLS = settings.symbols
EXCHANGES = settings.exchanges
MIN_PROFIT_PERCENTAGE = settings.min_profit_percentage


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def print_dashboard(
    order_books: Dict[Tuple[str, str], object],
    symbols: list[str],
    exchanges: list[str],
    opportunities: list,
) -> None:
    """Print the current arbitrage monitoring dashboard."""

    total_books = len(order_books)
    max_possible = len(symbols) * len(exchanges)

    print("\n" + "=" * 70)
    print(
        f" ARBIX LIVE MONITORING | "
        f"Active Streams: {total_books}/{max_possible}"
    )
    print("=" * 70)

    print(
        f"{'SYMBOL':<10} | "
        f"{'BUY AT':<8} | "
        f"{'SELL AT':<8} | "
        f"{'BEST SPREAD':<12} | "
        f"{'NET PROFIT':<10}"
    )

    print("-" * 70)

    for symbol in symbols:
        symbol_opportunities = [
            opportunity
            for opportunity in opportunities
            if opportunity.symbol == symbol
        ]

        if not symbol_opportunities:
            print(
                f"{symbol:<10} | "
                f"{'N/A':<8} | "
                f"{'N/A':<8} | "
                f"{'Waiting data':<12} | "
                f"{'N/A':<10}"
            )
            continue

        best_opportunity = max(
            symbol_opportunities,
            key=lambda opportunity: opportunity.gross_spread_pct,
        )

        if getattr(best_opportunity, "is_profitable", False):
            status = "YES"
        else:
            status = f"{best_opportunity.net_spread_pct:+.3f}%"

        print(
            f"{symbol:<10} | "
            f"{best_opportunity.buy_exchange:<8} | "
            f"{best_opportunity.sell_exchange:<8} | "
            f"{best_opportunity.gross_spread_pct:+.3f}%       | "
            f"{status:<10}"
        )

    print("=" * 70)

    print(
        f"Target Profit Threshold: "
        f">={MIN_PROFIT_PERCENTAGE}% "
        f"(Listening for opportunities...)\n"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    """Initialize ArbiX and start market monitoring."""

    logger.info(
        "Initializing ArbiX Bot | "
        f"Symbols: {SYMBOLS} | "
        f"Exchanges: {EXCHANGES}"
    )

    streamer = MarketDataStreamer(
        exchanges=EXCHANGES,
        symbols=SYMBOLS,
    )

    tasks: list[asyncio.Task] = []

    for exchange in EXCHANGES:
        for symbol in SYMBOLS:
            task = asyncio.create_task(
                streamer.watch_exchange_symbol_order_book(
                    exchange,
                    symbol,
                )
            )
            tasks.append(task)

    logger.info(
        "Starting market streams and arbitrage scanning loop..."
    )

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
        logger.info(
            "Stopping bot and closing exchange streams..."
        )

    finally:
        for task in tasks:
            task.cancel()

        await streamer.close_all()

        logger.info("ArbiX Bot stopped cleanly.")


if __name__ == "__main__":
    asyncio.run(main())