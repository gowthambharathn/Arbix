"""
ArbiX Order Book Models

Defines normalized order-book structures used internally by ArbiX,
independent of any specific cryptocurrency exchange.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable


@dataclass(frozen=True)
class OrderBookLevel:
    """Represents a single price level in an order book."""

    price: Decimal
    quantity: Decimal

    def __post_init__(self) -> None:
        if self.price <= 0:
            raise ValueError("Order-book price must be greater than zero.")

        if self.quantity <= 0:
            raise ValueError(
                "Order-book quantity must be greater than zero."
            )

    @property
    def value(self) -> Decimal:
        """Return the notional value represented by this level."""
        return self.price * self.quantity


@dataclass(frozen=True)
class OrderBook:
    """
    Normalized order book for a trading pair.

    Bids represent prices buyers are willing to pay.
    Asks represent prices sellers are willing to accept.
    """

    symbol: str
    bids: tuple[OrderBookLevel, ...]
    asks: tuple[OrderBookLevel, ...]
    timestamp: float

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("Order-book symbol cannot be empty.")

        if self.timestamp <= 0:
            raise ValueError("Order-book timestamp must be positive.")

    @property
    def best_bid(self) -> OrderBookLevel | None:
        """Return the highest available bid."""
        if not self.bids:
            return None
        return max(self.bids, key=lambda level: level.price)

    @property
    def best_ask(self) -> OrderBookLevel | None:
        """Return the lowest available ask."""
        if not self.asks:
            return None
        return min(self.asks, key=lambda level: level.price)

    # --- Compatibility methods for existing code callers ---
    def get_best_bid(self) -> tuple[float, float]:
        """Return best bid as (price, quantity) tuple."""
        bb = self.best_bid
        return (float(bb.price), float(bb.quantity)) if bb else (0.0, 0.0)

    def get_best_ask(self) -> tuple[float, float]:
        """Return best ask as (price, quantity) tuple."""
        ba = self.best_ask
        return (float(ba.price), float(ba.quantity)) if ba else (0.0, 0.0)

    @property
    def spread(self) -> Decimal | None:
        """Return the absolute bid/ask spread."""
        best_bid = self.best_bid
        best_ask = self.best_ask

        if best_bid is None or best_ask is None:
            return None

        return best_ask.price - best_bid.price

    @property
    def spread_percentage(self) -> Decimal | None:
        """Return the bid/ask spread as a percentage of the best bid."""
        best_bid = self.best_bid
        spread = self.spread

        if best_bid is None or spread is None or best_bid.price <= 0:
            return None

        return (spread / best_bid.price) * Decimal("100")

    def bid_proceeds(self, quantity: Decimal) -> Decimal:
        """Calculate total value available across bid levels."""
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        remaining = quantity
        total_value = Decimal("0")

        for level in sorted(self.bids, key=lambda item: item.price, reverse=True):
            if remaining <= 0:
                break
            filled_quantity = min(level.quantity, remaining)
            total_value += filled_quantity * level.price
            remaining -= filled_quantity

        return total_value

    def ask_cost(self, quantity: Decimal) -> Decimal:
        """Calculate the cost of buying a quantity from the ask side."""
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        remaining = quantity
        total_cost = Decimal("0")

        for level in sorted(self.asks, key=lambda item: item.price):
            if remaining <= 0:
                break
            filled_quantity = min(level.quantity, remaining)
            total_cost += filled_quantity * level.price
            remaining -= filled_quantity

        if remaining > 0:
            raise ValueError(
                f"Insufficient ask liquidity for {quantity} {self.base_asset}."
            )

        return total_cost

    def bid_value(self, quantity: Decimal) -> Decimal:
        """Calculate proceeds from selling a quantity into the bids."""
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        remaining = quantity
        total_value = Decimal("0")

        for level in sorted(self.bids, key=lambda item: item.price, reverse=True):
            if remaining <= 0:
                break
            filled_quantity = min(level.quantity, remaining)
            total_value += filled_quantity * level.price
            remaining -= filled_quantity

        if remaining > 0:
            raise ValueError(
                f"Insufficient bid liquidity for {quantity} {self.base_asset}."
            )

        return total_value

    @property
    def base_asset(self) -> str:
        """Return base asset (e.g. BTC from BTC/USDT)."""
        return self.symbol.split("/", maxsplit=1)[0]

    @property
    def quote_asset(self) -> str:
        """Return quote asset (e.g. USDT from BTC/USDT)."""
        parts = self.symbol.split("/", maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"Invalid trading pair format: {self.symbol}")
        return parts[1]


def create_order_book(
    symbol: str,
    bids: Iterable[tuple[Decimal | float | str, Decimal | float | str]],
    asks: Iterable[tuple[Decimal | float | str, Decimal | float | str]],
    timestamp: float,
) -> OrderBook:
    """Create a normalized OrderBook instance from raw price/quantity sequences."""
    return OrderBook(
        symbol=symbol,
        bids=tuple(
            OrderBookLevel(price=Decimal(str(price)), quantity=Decimal(str(quantity)))
            for price, quantity in bids
        ),
        asks=tuple(
            OrderBookLevel(price=Decimal(str(price)), quantity=Decimal(str(quantity)))
            for price, quantity in asks
        ),
        timestamp=timestamp,
    )