"""
ArbiX Order Management

Defines order models and manages the lifecycle of orders submitted
by the execution engine.

This module does not communicate directly with exchanges.
Exchange communication belongs to the execution layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import uuid4


class OrderSide(str, Enum):
    """Order direction."""

    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Supported order types."""

    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(str, Enum):
    """Lifecycle state of an order."""

    CREATED = "created"
    SUBMITTED = "submitted"
    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class Order:
    """
    Represents an order managed by ArbiX.

    The order object stores the local state of an exchange order.
    """

    exchange: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal

    price: Decimal | None = None

    order_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    exchange_order_id: str | None = None

    status: OrderStatus = OrderStatus.CREATED

    filled_quantity: Decimal = Decimal("0")
    average_fill_price: Decimal = Decimal("0")

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        """Validate the order."""

        if not self.exchange:
            raise ValueError(
                "Exchange cannot be empty."
            )

        if not self.symbol:
            raise ValueError(
                "Symbol cannot be empty."
            )

        if self.quantity <= 0:
            raise ValueError(
                "Order quantity must be greater than zero."
            )

        if self.price is not None and self.price <= 0:
            raise ValueError(
                "Order price must be greater than zero."
            )

        if self.filled_quantity < 0:
            raise ValueError(
                "Filled quantity cannot be negative."
            )

        if self.filled_quantity > self.quantity:
            raise ValueError(
                "Filled quantity cannot exceed order quantity."
            )

    @property
    def remaining_quantity(self) -> Decimal:
        """Return the quantity that remains unfilled."""

        return max(
            Decimal("0"),
            self.quantity - self.filled_quantity,
        )

    @property
    def fill_percentage(self) -> Decimal:
        """Return the percentage of the order that has been filled."""

        if self.quantity <= 0:
            return Decimal("0")

        return (
            self.filled_quantity
            / self.quantity
            * Decimal("100")
        )

    @property
    def is_terminal(self) -> bool:
        """
        Return whether the order has reached a final state.
        """

        return self.status in {
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
            OrderStatus.FAILED,
            OrderStatus.EXPIRED,
        }

    @property
    def is_active(self) -> bool:
        """Return whether the order can still change state."""

        return not self.is_terminal

    def update_fill(
        self,
        filled_quantity: Decimal,
        average_fill_price: Decimal,
    ) -> None:
        """
        Update the order with new fill information.

        Args:
            filled_quantity:
                Total quantity filled so far.

            average_fill_price:
                Average execution price of filled quantity.
        """

        if filled_quantity < 0:
            raise ValueError(
                "Filled quantity cannot be negative."
            )

        if filled_quantity > self.quantity:
            raise ValueError(
                "Filled quantity cannot exceed order quantity."
            )

        if average_fill_price < 0:
            raise ValueError(
                "Average fill price cannot be negative."
            )

        self.filled_quantity = filled_quantity
        self.average_fill_price = average_fill_price

        if filled_quantity == 0:
            self.status = OrderStatus.PENDING

        elif filled_quantity < self.quantity:
            self.status = OrderStatus.PARTIALLY_FILLED

        else:
            self.status = OrderStatus.FILLED

        self._touch()

    def mark_submitted(
        self,
        exchange_order_id: str,
    ) -> None:
        """
        Mark the order as successfully submitted.

        Args:
            exchange_order_id:
                Order identifier returned by the exchange.
        """

        if not exchange_order_id:
            raise ValueError(
                "Exchange order ID cannot be empty."
            )

        self.exchange_order_id = exchange_order_id
        self.status = OrderStatus.SUBMITTED

        self._touch()

    def mark_cancel_requested(self) -> None:
        """Mark the order as awaiting cancellation."""

        if self.is_terminal:
            return

        self.status = OrderStatus.CANCEL_REQUESTED
        self._touch()

    def mark_cancelled(self) -> None:
        """Mark the order as cancelled."""

        if self.status == OrderStatus.FILLED:
            raise ValueError(
                "A filled order cannot be cancelled."
            )

        self.status = OrderStatus.CANCELLED
        self._touch()

    def mark_rejected(self) -> None:
        """Mark the order as rejected by the exchange."""

        if self.is_terminal:
            return

        self.status = OrderStatus.REJECTED
        self._touch()

    def mark_failed(self) -> None:
        """Mark the order as failed."""

        if self.is_terminal:
            return

        self.status = OrderStatus.FAILED
        self._touch()

    def mark_expired(self) -> None:
        """Mark the order as expired."""

        if self.is_terminal:
            return

        self.status = OrderStatus.EXPIRED
        self._touch()

    def _touch(self) -> None:
        """Update the modification timestamp."""

        self.updated_at = datetime.now(timezone.utc)


class OrderManager:
    """
    Maintains locally tracked orders.

    The manager provides:
        - Order registration
        - Order lookup
        - State updates
        - Active-order tracking
        - Terminal-order tracking
    """

    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}

    def create_order(
        self,
        exchange: str,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        price: Decimal | None = None,
    ) -> Order:
        """
        Create and register a new local order.
        """

        order = Order(
            exchange=exchange,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )

        self._orders[order.order_id] = order

        return order

    def add_order(self, order: Order) -> None:
        """Register an existing order."""

        if order.order_id in self._orders:
            raise ValueError(
                f"Order already exists: {order.order_id}"
            )

        self._orders[order.order_id] = order

    def get_order(self, order_id: str) -> Order | None:
        """Return an order by its local ID."""

        return self._orders.get(order_id)

    def get_required_order(self, order_id: str) -> Order:
        """
        Return an order or raise an error if it does not exist.
        """

        order = self.get_order(order_id)

        if order is None:
            raise KeyError(
                f"Order not found: {order_id}"
            )

        return order

    def update_fill(
        self,
        order_id: str,
        filled_quantity: Decimal,
        average_fill_price: Decimal,
    ) -> Order:
        """Update fill information for an existing order."""

        order = self.get_required_order(order_id)

        order.update_fill(
            filled_quantity=filled_quantity,
            average_fill_price=average_fill_price,
        )

        return order

    def mark_submitted(
        self,
        order_id: str,
        exchange_order_id: str,
    ) -> Order:
        """Mark an order as submitted."""

        order = self.get_required_order(order_id)

        order.mark_submitted(
            exchange_order_id=exchange_order_id,
        )

        return order

    def mark_cancel_requested(
        self,
        order_id: str,
    ) -> Order:
        """Mark an order as awaiting cancellation."""

        order = self.get_required_order(order_id)
        order.mark_cancel_requested()

        return order

    def mark_cancelled(
        self,
        order_id: str,
    ) -> Order:
        """Mark an order as cancelled."""

        order = self.get_required_order(order_id)
        order.mark_cancelled()

        return order

    def mark_rejected(
        self,
        order_id: str,
    ) -> Order:
        """Mark an order as rejected."""

        order = self.get_required_order(order_id)
        order.mark_rejected()

        return order

    def mark_failed(
        self,
        order_id: str,
    ) -> Order:
        """Mark an order as failed."""

        order = self.get_required_order(order_id)
        order.mark_failed()

        return order

    def mark_expired(
        self,
        order_id: str,
    ) -> Order:
        """Mark an order as expired."""

        order = self.get_required_order(order_id)
        order.mark_expired()

        return order

    def get_active_orders(self) -> list[Order]:
        """Return all orders that are still active."""

        return [
            order
            for order in self._orders.values()
            if order.is_active
        ]

    def get_terminal_orders(self) -> list[Order]:
        """Return orders that have reached a final state."""

        return [
            order
            for order in self._orders.values()
            if order.is_terminal
        ]

    def get_all_orders(self) -> list[Order]:
        """Return all tracked orders."""

        return list(self._orders.values())

    def remove_order(self, order_id: str) -> Order:
        """
        Remove an order from local tracking.

        This should generally only be used for cleanup operations.
        """

        try:
            return self._orders.pop(order_id)
        except KeyError as error:
            raise KeyError(
                f"Order not found: {order_id}"
            ) from error

    def count_active_orders(self) -> int:
        """Return the number of active orders."""

        return len(self.get_active_orders())