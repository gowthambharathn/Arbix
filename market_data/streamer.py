"""
ArbiX Market Data Streamer

Asynchronously streams live order book data across exchanges using CCXT Pro.
Includes automatic reconnection logic and exception handling.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict, List

import ccxt.pro as ccxtpro
from market_data.order_book import OrderBook, create_order_book

logger = logging.getLogger("ArbiX.Streamer")


class MarketDataStreamer:
    """
    Streams live order book updates from exchanges via WebSockets.
    """

    def __init__(
        self,
        exchanges: List[str],
        symbol: str,
    ) -> None:
        self.symbol = symbol
        self.exchanges_instances: Dict[str, ccxtpro.Exchange] = {}
        self.order_books: Dict[str, OrderBook] = {}

        for ex_name in exchanges:
            try:
                exchange_class = getattr(ccxtpro, ex_name)
                self.exchanges_instances[ex_name] = exchange_class(
                    {"enableRateLimit": True}
                )
            except AttributeError:
                logger.error(f"Exchange '{ex_name}' is not supported by CCXT Pro.")

    async def watch_exchange_order_book(self, ex_name: str) -> None:
        """Continuously watch order book streams for a specific exchange with auto-reconnect."""
        exchange = self.exchanges_instances[ex_name]

        while True:
            try:
                ccxt_orderbook = await exchange.watch_order_book(self.symbol)

                bids = ccxt_orderbook.get("bids", [])
                asks = ccxt_orderbook.get("asks", [])

                raw_timestamp = ccxt_orderbook.get("timestamp")
                timestamp = (
                    float(raw_timestamp) / 1000.0
                    if raw_timestamp
                    else time.time()
                )

                self.order_books[ex_name] = create_order_book(
                    symbol=self.symbol,
                    bids=bids,
                    asks=asks,
                    timestamp=timestamp,
                )
                logger.debug(f"[{ex_name}] Order book updated for {self.symbol}")

            except asyncio.CancelledError:
                logger.info(f"[{ex_name}] Stream watcher task cancelled.")
                break
            except Exception as error:
                logger.error(
                    f"[{ex_name}] Stream error: {error}. Retrying in 3 seconds..."
                )
                await asyncio.sleep(3)

        await exchange.close()

    async def close_all(self) -> None:
        """Close all active exchange WebSocket connections."""
        for ex_name, exchange in self.exchanges_instances.items():
            try:
                await exchange.close()
            except Exception as error:
                logger.error(f"Error closing exchange connection for {ex_name}: {error}")