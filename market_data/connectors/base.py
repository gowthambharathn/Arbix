"""
Abstract Base Class for Async Exchange WebSocket Connectors.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Callable, Coroutine, Any

from market_data.order_book import OrderBook

logger = logging.getLogger("arbix.connectors")


class BaseExchangeConnector(ABC):
    """Abstract connector managing WebSocket connections and order book normalization."""

    def __init__(self, exchange_id: str, symbol: str) -> None:
        self.exchange_id = exchange_id
        self.symbol = symbol
        self._running = False
        self._task: asyncio.Task | None = None
        self._callbacks: list[Callable[[OrderBook], Coroutine[Any, Any, None]]] = []

    def register_callback(
        self, callback: Callable[[OrderBook], Coroutine[Any, Any, None]]
    ) -> None:
        """Register an async callback triggered whenever a normalized OrderBook updates."""
        self._callbacks.append(callback)

    async def _notify_subscribers(self, order_book: OrderBook) -> None:
        """Forward updated OrderBook to all registered listeners."""
        for callback in self._callbacks:
            try:
                await callback(order_book)
            except Exception as e:
                logger.error(f"Error executing callback in {self.exchange_id}: {e}")

    @abstractmethod
    async def connect(self) -> None:
        """Establishes WebSocket connection and starts reading incoming frames."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Gracefully disconnects the WebSocket stream."""
        pass