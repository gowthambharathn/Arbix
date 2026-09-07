"""
ArbiX Application Entry Point — Live WebSocket Engine.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
import time
from types import FrameType

from config.settings import Settings, load_settings
from market_data.connectors import BinanceConnector, CoinbaseConnector
from market_data.order_book import OrderBook, create_order_book

logger = logging.getLogger("arbix")


class ArbiXApplication:
    """Main ArbiX pipeline runner with live WebSocket pricing."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._shutdown_event = asyncio.Event()
        self._running = False
        self._tasks: list[asyncio.Task] = []

        now = time.time()
        self.binance_book: OrderBook = create_order_book("BTC/USDT", [], [], now)
        self.coinbase_book: OrderBook = create_order_book("BTC/USDT", [], [], now)

        # Connectors
        self.binance_conn = BinanceConnector(symbol="BTC/USDT")
        self.coinbase_conn = CoinbaseConnector(symbol="BTC/USDT")

        # Callbacks
        self.binance_conn.register_callback(self._on_binance_update)
        self.coinbase_conn.register_callback(self._on_coinbase_update)

        self._cycle = 0

    async def _on_binance_update(self, book: OrderBook) -> None:
        self.binance_book = book
        await self._check_arbitrage()

    async def _on_coinbase_update(self, book: OrderBook) -> None:
        self.coinbase_book = book
        await self._check_arbitrage()

    async def _check_arbitrage(self) -> None:
        """Calculates current spread between Binance and Coinbase order books."""
        best_buy = self.binance_book.best_ask
        best_sell = self.coinbase_book.best_bid

        if not best_buy or not best_sell:
            return

        self._cycle += 1
        best_buy_price = float(best_buy.price)
        best_sell_price = float(best_sell.price)

        gross_spread = best_sell_price - best_buy_price
        gross_pct = (gross_spread / best_buy_price) * 100 if best_buy_price else 0.0

        # Estimated combined fees (~0.20%)
        estimated_fees = (best_buy_price * 0.001) + (best_sell_price * 0.001)
        net_profit = gross_spread - estimated_fees
        net_pct = (net_profit / best_buy_price) * 100 if best_buy_price else 0.0

        min_profit_pct = float(getattr(self.settings, "min_profit_percentage", 0.20))

        if net_profit > 0 and net_pct >= min_profit_pct:
            msg = (
                f"\033[92m[LIVE PROFIT DETECTED] Cycle {self._cycle} | Pair: BTC/USDT | "
                f"Buy (Binance): ${best_buy_price:.2f} | Sell (Coinbase): ${best_sell_price:.2f} | "
                f"Net Profit: ${net_profit:.2f} ({net_pct:.2f}%)\033[0m"
            )
            logger.info(msg)
        else:
            msg = (
                f"[LIVE SCANNING] Cycle {self._cycle} | Pair: BTC/USDT | "
                f"Buy: ${best_buy_price:.2f} | Sell: ${best_sell_price:.2f} | "
                f"Spread: ${gross_spread:.2f} ({gross_pct:.2f}%)"
            )
            logger.info(msg)

    async def start(self) -> None:
        """Start WebSocket connections."""
        if self._running:
            return

        self._running = True
        logger.info("=== ArbiX Live Pipeline Started ===")

        self._tasks.append(asyncio.create_task(self.binance_conn.connect()))
        self._tasks.append(asyncio.create_task(self.coinbase_conn.connect()))

    async def run(self) -> None:
        await self.start()
        try:
            await self._shutdown_event.wait()
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        if not self._running:
            return

        logger.info("Shutting down ArbiX connectors...")
        self._running = False

        await self.binance_conn.close()
        await self.coinbase_conn.close()

        for task in self._tasks:
            task.cancel()

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        logger.info("ArbiX pipeline safely terminated.")

    def request_shutdown(self) -> None:
        if not self._shutdown_event.is_set():
            self._shutdown_event.set()


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
        force=True,
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