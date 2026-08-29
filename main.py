"""
ArbiX Application Entry Point.
"""

from __future__ import annotations

import asyncio
import logging
import random
import signal
import sys
import time
from decimal import Decimal
from types import FrameType

from config.settings import Settings, load_settings
from market_data.order_book import OrderBook, create_order_book

logger = logging.getLogger("arbix")


class ArbiXApplication:
    """Main ArbiX pipeline runner with real-time price monitoring simulation."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._shutdown_event = asyncio.Event()
        self._running = False
        self._tasks: list[asyncio.Task] = []

        now = time.time()
        self.binance_book: OrderBook = create_order_book("BTC/USDT", [], [], now)
        self.coinbase_book: OrderBook = create_order_book("BTC/USDT", [], [], now)

    async def _market_data_simulator(self) -> None:
        """Simulates price ticks and checks for real-time arbitrage spreads."""
        base_btc_price = 100000.0
        cycle = 0

        while self._running:
            try:
                cycle += 1
                now = time.time()

                # Generate dynamic spread opportunities
                binance_ask = base_btc_price + random.uniform(-100, 50)
                coinbase_bid = base_btc_price + random.uniform(200, 800)

                # Re-create fresh immutable order books each tick
                self.binance_book = create_order_book(
                    symbol="BTC/USDT",
                    bids=[(binance_ask - 10, 2.0)],
                    asks=[(binance_ask, 2.0)],
                    timestamp=now,
                )

                self.coinbase_book = create_order_book(
                    symbol="BTC/USDT",
                    bids=[(coinbase_bid, 2.0)],
                    asks=[(coinbase_bid + 10, 2.0)],
                    timestamp=now,
                )

                best_buy = self.binance_book.best_ask
                best_sell = self.coinbase_book.best_bid

                if best_buy and best_sell:
                    best_buy_price = float(best_buy.price)
                    best_sell_price = float(best_sell.price)

                    gross_spread = best_sell_price - best_buy_price
                    gross_pct = (gross_spread / best_buy_price) * 100

                    # Standard combined trading fee (~0.20%)
                    estimated_fees = (best_buy_price * 0.001) + (best_sell_price * 0.001)
                    net_profit = gross_spread - estimated_fees
                    net_pct = (net_profit / best_buy_price) * 100

                    min_profit_pct = float(getattr(self.settings, "min_profit_percentage", 0.20))

                    if net_profit > 0 and net_pct >= min_profit_pct:
                        msg = (
                            f"[PROFIT DETECTED] Cycle {cycle} | Pair: BTC/USDT | "
                            f"Buy (Binance): ${best_buy_price:.2f} | Sell (Coinbase): ${best_sell_price:.2f} | "
                            f"Net Profit: ${net_profit:.2f} ({net_pct:.2f}%)"
                        )
                        logger.info(msg)
                        print(f"\033[92m{msg}\033[0m", flush=True)  # Green text output
                    else:
                        msg = (
                            f"[SCANNING] Cycle {cycle} | Pair: BTC/USDT | "
                            f"Buy: ${best_buy_price:.2f} | Sell: ${best_sell_price:.2f} | "
                            f"Spread: ${gross_spread:.2f} ({gross_pct:.2f}%)"
                        )
                        logger.info(msg)
                        print(msg, flush=True)

            except Exception as e:
                print(f"[ERROR in Simulator]: {e}", flush=True)

            await asyncio.sleep(1)

    async def start(self) -> None:
        """Start the pipeline."""
        if self._running:
            return

        self._running = True
        print("=== ArbiX Pipeline Started ===", flush=True)

        sim_task = asyncio.create_task(self._market_data_simulator())
        self._tasks.append(sim_task)

    async def run(self) -> None:
        await self.start()
        try:
            await self._shutdown_event.wait()
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        if not self._running:
            return

        print("\nShutting down ArbiX...", flush=True)
        self._running = False

        for task in self._tasks:
            task.cancel()

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        print("ArbiX shutdown completed.", flush=True)

    def request_shutdown(self) -> None:
        if not self._shutdown_event.is_set():
            self._shutdown_event.set()


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
    )


def install_signal_handlers(application: ArbiXApplication) -> None:
    loop = asyncio.get_running_loop()

    def handle_signal(signum: int, frame: FrameType | None = None) -> None:
        application.request_shutdown()

    for signal_name in ("SIGINT", "SIGTERM"):
        signal_value = getattr(signal, signal_name, None)
        if signal_value is not None:
            try:
                loop.add_signal_handler(signal_value, handle_signal, signal_value)
            except (NotImplementedError, AttributeError):
                try:
                    signal.signal(signal_value, handle_signal)
                except (ValueError, OSError):
                    pass


async def async_main() -> None:
    settings = load_settings()
    configure_logging(settings)
    application = ArbiXApplication(settings=settings)
    install_signal_handlers(application)
    await application.run()


def main() -> None:
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nArbiX interrupted by user.", flush=True)


if __name__ == "__main__":
    main()