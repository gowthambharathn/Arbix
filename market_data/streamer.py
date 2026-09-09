"""
ArbiX Market Data Streamer

Asynchronously streams live order book data across multiple pairs and exchanges using CCXT Pro.
Includes automatic market validation, reconnection logic, and exception handling.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict, List, Set, Tuple

import ccxt.pro as ccxtpro
from ccxt.base.errors import BadSymbol
from market_data.order_book import OrderBook, create_order_book

logger = logging.getLogger("ArbiX.Streamer")


class MarketDataStreamer:
    """
    Streams live order book updates from exchanges via WebSockets for multiple symbols.
    """

    def __init__(
        self,
        exchanges: List[str],
        symbols: List[str],
    ) -> None:
        self.symbols = symbols
        self.exchanges_instances: Dict[str, ccxtpro.Exchange] = {}
        # Keys are tuples of (exchange_name, symbol) -> OrderBook
        self.order_books: Dict[Tuple[str, str], OrderBook] = {}
        # Tracks initialized market dynamic validation per exchange
        self._loaded_markets: Set[str] = set()

        for ex_name in exchanges:
            try:
                exchange_class = getattr(ccxtpro, ex_name)
                self.exchanges_instances[ex_name] = exchange_class(
                    {"enableRateLimit": True}
                )
            except AttributeError:
                logger.error(f"Exchange '{ex_name}' is not supported by CCXT Pro.")

    async def _ensure_markets_loaded(self, ex_name: str) -> bool:
        """Fetch and cache market metadata for the given exchange."""
        if ex_name in self._loaded_markets:
            return True

        exchange = self.exchanges_instances[ex_name]
        try:
            await exchange.load_markets()
            self._loaded_markets.add(ex_name)
            return True
        except Exception as error:
            logger.error(f"[{ex_name}] Failed to load market metadata: {error}")
            return False

    async def watch_exchange_symbol_order_book(self, ex_name: str, symbol: str) -> None:
        """Continuously watch order book stream for a specific exchange and symbol."""
        exchange = self.exchanges_instances[ex_name]

        # Verify market exists on this exchange before entering stream loop
        markets_ready = await self._ensure_markets_loaded(ex_name)
        if markets_ready and symbol not in exchange.markets:
            logger.warning(
                f"[{ex_name}] Skipping stream: Market pair '{symbol}' is not listed on this exchange."
            )
            return

        while True:
            try:
                ccxt_orderbook = await exchange.watch_order_book(symbol)

                bids = ccxt_orderbook.get("bids", [])
                asks = ccxt_orderbook.get("asks", [])

                raw_timestamp = ccxt_orderbook.get("timestamp")
                timestamp = (
                    float(raw_timestamp) / 1000.0
                    if raw_timestamp
                    else time.time()
                )

                self.order_books[(ex_name, symbol)] = create_order_book(
                    symbol=symbol,
                    bids=bids,
                    asks=asks,
                    timestamp=timestamp,
                )
                logger.debug(f"[{ex_name}] Order book updated for {symbol}")

            except BadSymbol:
                logger.warning(
                    f"[{ex_name} | {symbol}] Market symbol not supported by exchange. Terminating task."
                )
                break
            except asyncio.CancelledError:
                logger.info(f"[{ex_name} | {symbol}] Stream watcher task cancelled.")
                break
            except Exception as error:
                logger.error(
                    f"[{ex_name} | {symbol}] Stream error: {error}. Retrying in 3 seconds..."
                )
                await asyncio.sleep(3)

    async def close_all(self) -> None:
        """Close all active exchange WebSocket connections."""
        for ex_name, exchange in self.exchanges_instances.items():
            try:
                await exchange.close()
            except Exception as error:
                logger.error(f"Error closing exchange connection for {ex_name}: {error}")