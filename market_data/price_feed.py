"""
ArbiX Price Feed

Defines normalized market-price models and the interface used by
the market-data layer.

Exchange-specific implementations should convert their raw market
data into these models before passing it to the rest of ArbiX.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from time import time
from typing import AsyncIterator, Iterable


@dataclass(frozen=True)
class PriceTick:
    """
    Represents a normalized market price update.

    Attributes:
        exchange: Name of the exchange that produced the tick.
        symbol: Trading pair, for example BTC/USDT.
        bid: Highest price currently offered by buyers.
        ask: Lowest price currently offered by sellers.
        timestamp: Unix timestamp when the market data was received.
    """

    exchange: str
    symbol: str
    bid: Decimal
    ask: Decimal
    timestamp: float

    def __post_init__(self) -> None:
        if not self.exchange:
            raise ValueError("Exchange name cannot be empty.")

        if not self.symbol:
            raise ValueError("Trading symbol cannot be empty.")

        if self.bid <= 0:
            raise ValueError("Bid price must be greater than zero.")

        if self.ask <= 0:
            raise ValueError("Ask price must be greater than zero.")

        if self.ask < self.bid:
            raise ValueError(
                "Ask price cannot be lower than bid price."
            )

        if self.timestamp <= 0:
            raise ValueError("Timestamp must be greater than zero.")

    @property
    def spread(self) -> Decimal:
        """Return the absolute bid/ask spread."""

        return self.ask - self.bid

    @property
    def spread_percentage(self) -> Decimal:
        """Return the bid/ask spread as a percentage."""

        return (self.spread / self.bid) * Decimal("100")

    @property
    def mid_price(self) -> Decimal:
        """Return the midpoint between the bid and ask."""

        return (self.bid + self.ask) / Decimal("2")

    @property
    def age(self) -> float:
        """Return the approximate age of this price update in seconds."""

        return max(0.0, time() - self.timestamp)

    def is_stale(self, max_age_seconds: float) -> bool:
        """
        Determine whether this price update is stale.

        Args:
            max_age_seconds: Maximum acceptable age in seconds.

        Returns:
            True when the price is older than the allowed threshold.
        """

        if max_age_seconds <= 0:
            raise ValueError(
                "max_age_seconds must be greater than zero."
            )

        return self.age > max_age_seconds


class PriceFeedError(Exception):
    """Base exception for price-feed errors."""


class PriceFeedUnavailableError(PriceFeedError):
    """Raised when price data is temporarily unavailable."""


class PriceFeed(ABC):
    """
    Abstract interface for market-price providers.

    Implementations may use REST APIs, WebSockets, or another
    market-data source.
    """

    @abstractmethod
    async def get_latest_price(
        self,
        symbol: str,
    ) -> PriceTick:
        """
        Get the latest price for a trading pair.

        Args:
            symbol: Trading pair such as BTC/USDT.

        Returns:
            Latest normalized price tick.
        """

    @abstractmethod
    async def subscribe(
        self,
        symbols: Iterable[str],
    ) -> AsyncIterator[PriceTick]:
        """
        Subscribe to continuous price updates.

        Args:
            symbols: Trading pairs to monitor.

        Yields:
            Normalized price updates.
        """

    @abstractmethod
    async def close(self) -> None:
        """Release resources used by the price feed."""


class InMemoryPriceFeed(PriceFeed):
    """
    Simple in-memory price feed for development and testing.

    This implementation does not connect to a real exchange.
    It allows other ArbiX components to be developed and tested
    without external network dependencies.
    """

    def __init__(self) -> None:
        self._prices: dict[str, PriceTick] = {}
        self._closed = False

    def update(self, price: PriceTick) -> None:
        """
        Store or replace the latest price for a symbol.

        Args:
            price: Normalized price tick.
        """

        if self._closed:
            raise PriceFeedError(
                "Cannot update a closed price feed."
            )

        key = self._build_key(
            exchange=price.exchange,
            symbol=price.symbol,
        )

        self._prices[key] = price

    async def get_latest_price(
        self,
        symbol: str,
    ) -> PriceTick:
        """
        Return the latest stored price.

        Args:
            symbol: Trading pair.

        Returns:
            Latest price tick.

        Raises:
            PriceFeedUnavailableError:
                If no price has been stored for the symbol.
        """

        if self._closed:
            raise PriceFeedError(
                "Price feed is closed."
            )

        matches = [
            price
            for price in self._prices.values()
            if price.symbol == symbol
        ]

        if not matches:
            raise PriceFeedUnavailableError(
                f"No price available for {symbol}."
            )

        return max(
            matches,
            key=lambda price: price.timestamp,
        )

    async def subscribe(
        self,
        symbols: Iterable[str],
    ) -> AsyncIterator[PriceTick]:
        """
        Yield currently stored prices matching the requested symbols.

        This is primarily intended for tests and local development.
        """

        if self._closed:
            raise PriceFeedError(
                "Price feed is closed."
            )

        requested_symbols = set(symbols)

        for price in self._prices.values():
            if price.symbol in requested_symbols:
                yield price

    async def close(self) -> None:
        """Close the in-memory price feed."""

        self._closed = True
        self._prices.clear()

    @staticmethod
    def _build_key(
        exchange: str,
        symbol: str,
    ) -> str:
        """Build a unique key for an exchange/symbol combination."""

        return f"{exchange}:{symbol}"