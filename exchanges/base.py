"""
ArbiX Exchange Abstractions

Defines the common interfaces and data models that all exchange
integrations must follow.

Exchange-specific implementations should inherit from these
interfaces rather than exposing exchange-specific behavior to
the rest of the application.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ExchangeError(Exception):
    """Base exception for exchange-related errors."""


class ExchangeConnectionError(ExchangeError):
    """Raised when communication with an exchange fails."""


class ExchangeAuthenticationError(ExchangeError):
    """Raised when exchange authentication fails."""


class ExchangeRateLimitError(ExchangeError):
    """Raised when an exchange rate limit is exceeded."""


class ExchangeOrderError(ExchangeError):
    """Raised when an exchange rejects or fails an order."""


class ExchangeOrderSide(str, Enum):
    """Supported exchange order sides."""

    BUY = "buy"
    SELL = "sell"


class ExchangeOrderType(str, Enum):
    """Supported exchange order types."""

    MARKET = "market"
    LIMIT = "limit"


@dataclass(frozen=True)
class Ticker:
    """
    Represents the latest ticker information for a trading pair.
    """

    exchange: str
    symbol: str

    bid: Decimal
    ask: Decimal

    timestamp: float

    @property
    def spread(self) -> Decimal:
        """Return the absolute bid/ask spread."""

        return self.ask - self.bid

    @property
    def mid_price(self) -> Decimal:
        """Return the midpoint between bid and ask."""

        return (self.bid + self.ask) / Decimal("2")

    def __post_init__(self) -> None:
        """Validate ticker data."""

        if not self.exchange:
            raise ValueError(
                "Exchange cannot be empty."
            )

        if not self.symbol:
            raise ValueError(
                "Symbol cannot be empty."
            )

        if self.bid <= 0:
            raise ValueError(
                "Bid price must be greater than zero."
            )

        if self.ask <= 0:
            raise ValueError(
                "Ask price must be greater than zero."
            )

        if self.ask < self.bid:
            raise ValueError(
                "Ask price cannot be lower than bid price."
            )

        if self.timestamp <= 0:
            raise ValueError(
                "Ticker timestamp must be greater than zero."
            )


@dataclass(frozen=True)
class TradingFee:
    """
    Represents trading fees for an exchange.

    Values are percentages expressed as decimal percentages.

    Example:

        Decimal("0.10") = 0.10%
    """

    maker: Decimal
    taker: Decimal

    def __post_init__(self) -> None:
        """Validate trading fees."""

        if self.maker < 0:
            raise ValueError(
                "Maker fee cannot be negative."
            )

        if self.taker < 0:
            raise ValueError(
                "Taker fee cannot be negative."
            )


@dataclass(frozen=True)
class OrderSubmission:
    """
    Normalized representation of an order submitted to an exchange.
    """

    exchange_order_id: str
    status: str

    filled_quantity: Decimal
    average_fill_price: Decimal

    message: str = ""


@dataclass(frozen=True)
class ExchangeBalance:
    """
    Represents an account balance on an exchange.
    """

    asset: str

    available: Decimal
    locked: Decimal

    @property
    def total(self) -> Decimal:
        """Return total balance."""

        return self.available + self.locked


class ExchangeClient(ABC):
    """
    Abstract interface for cryptocurrency exchange integrations.

    Every exchange implementation should provide these operations.

    The rest of ArbiX should depend on this interface rather than
    directly depending on an exchange SDK.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the normalized exchange name."""

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection or initialize the exchange client.
        """

    @abstractmethod
    async def close(self) -> None:
        """Close exchange connections and release resources."""

    @abstractmethod
    async def get_ticker(
        self,
        symbol: str,
    ) -> Ticker:
        """Return the latest ticker for a symbol."""

    @abstractmethod
    async def get_order_book(
        self,
        symbol: str,
    ):
        """
        Return the latest order book.

        The concrete return type will be connected to ArbiX's
        OrderBook model.
        """

    @abstractmethod
    async def get_balance(
        self,
        asset: str,
    ) -> ExchangeBalance:
        """Return the current balance for an asset."""

    @abstractmethod
    async def get_trading_fee(
        self,
        symbol: str,
    ) -> TradingFee:
        """Return maker/taker trading fees."""

    @abstractmethod
    async def submit_order(
        self,
        symbol: str,
        side: ExchangeOrderSide,
        order_type: ExchangeOrderType,
        quantity: Decimal,
        price: Decimal | None = None,
    ) -> OrderSubmission:
        """Submit an order to the exchange."""

    @abstractmethod
    async def cancel_order(
        self,
        exchange_order_id: str,
        symbol: str,
    ) -> OrderSubmission:
        """Cancel an existing exchange order."""

    @abstractmethod
    async def get_order(
        self,
        exchange_order_id: str,
        symbol: str,
    ) -> OrderSubmission:
        """Retrieve the latest state of an exchange order."""