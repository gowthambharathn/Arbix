"""
ArbiX Arbitrage Bot Main Entry Point

Coordinates order book WebSocket streaming, scans for opportunities,
evaluates profitability, and simulates paper trade executions.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from decimal import Decimal

from arbitrage.calculator import ProfitabilityCalculator
from arbitrage.finder import ArbitrageFinder
from config.settings import settings
from engine.paper_engine import PaperEngine
from market_data.streamer import MarketDataStreamer

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ArbiX.Main")


async def run_arbitrage_loop(
    streamer: MarketDataStreamer,
    finder: ArbitrageFinder,
    engine: PaperEngine,
    interval_seconds: float = 0.5,
) -> None:
    """Periodically check active order books and execute profitable trades."""
    logger.info("Starting arbitrage evaluation loop...")
    heartbeat_counter = 0

    try:
        while True:
            await asyncio.sleep(interval_seconds)
            heartbeat_counter += 1

            active_books_count = len(streamer.order_books)

            # Log heartbeat every ~10 seconds (20 iterations at 0.5s)
            if heartbeat_counter % 20 == 0:
                cached_exchanges = list(streamer.order_books.keys())
                logger.info(
                    f"Heartbeat | Cached Order Books ({active_books_count}/{len(streamer.exchanges_instances)}): "
                    f"{cached_exchanges}"
                )

            if active_books_count < 2:
                continue

            # Scan order books for profitable arbitrage opportunities
            opportunities = finder.find_opportunities(
                order_books=streamer.order_books,
                trade_quantity=Decimal(str(settings.max_trade_amount)),
            )

            for opportunity, result in opportunities:
                logger.info(
                    f"Found Opportunity | Route: {opportunity.buy_exchange} -> {opportunity.sell_exchange} | "
                    f"Gross Profit: ${result.gross_profit:.2f} | Net Profit: ${result.net_profit:.2f} "
                    f"({result.net_profit_percentage:.2f}%)"
                )

                # Execute via paper engine
                record = engine.execute_arbitrage(
                    opportunity=opportunity,
                    result=result,
                )

                if record:
                    summary = engine.get_performance_summary()
                    logger.info(
                        f"Performance Summary | Executed Trades: {summary['total_trades']} | "
                        f"Cumulative Profit: ${summary['total_net_profit']:.2f} | "
                        f"Current USDT Balance: ${summary['usdt_balance']:.2f}"
                    )

    except asyncio.CancelledError:
        logger.info("Arbitrage loop cancelled.")


async def main() -> None:
    """Main application lifecycle manager."""
    exchanges = settings.exchanges
    symbol = settings.symbol

    logger.info(
        f"Initializing ArbiX Bot | Symbol: {symbol} | Exchanges: {exchanges}"
    )

    calculator = ProfitabilityCalculator()
    finder = ArbitrageFinder(calculator=calculator)
    engine = PaperEngine()

    streamer = MarketDataStreamer(exchanges=exchanges, symbol=symbol)

    # Launch streaming tasks per exchange
    stream_tasks = [
        asyncio.create_task(streamer.watch_exchange_order_book(ex_name))
        for ex_name in streamer.exchanges_instances.keys()
    ]

    # Launch trade evaluation loop
    eval_task = asyncio.create_task(
        run_arbitrage_loop(streamer=streamer, finder=finder, engine=engine)
    )

    try:
        await asyncio.gather(*stream_tasks, eval_task)
    except KeyboardInterrupt:
        logger.info("Shutting down ArbiX engine...")
    finally:
        eval_task.cancel()
        for task in stream_tasks:
            task.cancel()
        await streamer.close_all()
        logger.info("Clean shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass