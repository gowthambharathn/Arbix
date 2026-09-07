"""
Coinbase Exchange Order Book WebSocket Connector.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import websockets

from market_data.connectors.base import BaseExchangeConnector
from market_data.order_book import create_order_book

logger = logging.getLogger("arbix.connectors.coinbase")


class CoinbaseConnector(BaseExchangeConnector):
    """Coinbase Advanced WebSocket connector streaming ticker data."""

    WS_URL = "wss://ws-feed.exchange.coinbase.com"

    def __init__(self, symbol: str = "BTC/USDT") -> None:
        # Convert BTC/USDT -> BTC-USD (Coinbase standard pair)
        formatted_symbol = symbol.replace("USDT", "USD").replace("/", "-")
        super().__init__(exchange_id="coinbase", symbol=symbol)
        self.product_id = formatted_symbol
        self._ws: websockets.WebSocketClientProtocol | None = None

    async def connect(self) -> None:
        """Connect to Coinbase WS feed and subscribe to ticker updates."""
        self._running = True
        logger.info(f"[Coinbase] Connecting to stream: {self.WS_URL}")

        while self._running:
            try:
                async with websockets.connect(self.WS_URL) as ws:
                    self._ws = ws
                    
                    # Subscribe to ticker channel
                    subscribe_msg = {
                        "type": "subscribe",
                        "product_ids": [self.product_id],
                        "channels": ["ticker"],
                    }
                    await ws.send(json.dumps(subscribe_msg))
                    logger.info(f"[Coinbase] Subscribed to {self.product_id} ticker channel")

                    async for message in ws:
                        if not self._running:
                            break

                        data = json.loads(message)

                        if data.get("type") == "ticker" and "best_bid" in data and "best_ask" in data:
                            now = time.time()
                            
                            bids = [(float(data["best_bid"]), float(data.get("best_bid_size", 1.0)))]
                            asks = [(float(data["best_ask"]), float(data.get("best_ask_size", 1.0)))]

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
                    logger.warning(f"[Coinbase] WebSocket error: {e}. Reconnecting in 3s...")
                    await asyncio.sleep(3)

    async def close(self) -> None:
        """Disconnect WebSocket connection."""
        self._running = False
        if self._ws:
            await self._ws.close()
        logger.info("[Coinbase] Connection closed.")