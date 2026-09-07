"""
Binance Spot Order Book WebSocket Connector.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import websockets

from market_data.connectors.base import BaseExchangeConnector
from market_data.order_book import create_order_book

logger = logging.getLogger("arbix.connectors.binance")


class BinanceConnector(BaseExchangeConnector):
    """Binance WebSocket connector streaming real-time order book ticks."""

    WS_BASE_URL = "wss://stream.binance.com:9443/ws"

    def __init__(self, symbol: str = "BTC/USDT") -> None:
        formatted_symbol = symbol.replace("/", "").lower()
        super().__init__(exchange_id="binance", symbol=symbol)
        self.stream_symbol = formatted_symbol
        self._ws: websockets.WebSocketClientProtocol | None = None

    async def connect(self) -> None:
        """Connect to Binance bookTicker stream and listen for order book events."""
        endpoint = f"{self.WS_BASE_URL}/{self.stream_symbol}@bookTicker"
        self._running = True

        logger.info(f"[Binance] Connecting to stream: {endpoint}")

        while self._running:
            try:
                async with websockets.connect(endpoint) as ws:
                    self._ws = ws
                    logger.info(f"[Binance] Stream connected successfully ({self.symbol})")

                    async for message in ws:
                        if not self._running:
                            break
                        
                        data = json.loads(message)
                        now = time.time()

                        # Binance payload mapping:
                        # 'b': best bid price, 'B': best bid qty
                        # 'a': best ask price, 'A': best ask qty
                        bids = [(float(data["b"]), float(data["B"]))]
                        asks = [(float(data["a"]), float(data["A"]))]

                        order_book = create_order_book(
                            symbol=self.symbol,
                            bids=bids,
                            asks=asks,
                            timestamp=now,
                        )

                        await self._notify_subscribers(order_book)

            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._running:
                    logger.warning(f"[Binance] WebSocket error: {e}. Reconnecting in 3s...")
                    await asyncio.sleep(3)

    async def close(self) -> None:
        """Disconnect WebSocket connection."""
        self._running = False
        if self._ws:
            await self._ws.close()
        logger.info("[Binance] Connection closed.")