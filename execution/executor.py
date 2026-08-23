"""
ArbiX Execution Engine

Provides the execution abstraction used by ArbiX to submit and manage
orders.

The execution engine is intentionally independent from any specific
cryptocurrency exchange. Exchange-specific API communication belongs
inside exchange adapters.

Supported modes:
    - PAPER: simulated execution
    - LIVE: real exchange execution
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

from execution.order_manager import (
    Order,
    OrderManager,
    OrderSide,
    OrderStatus,
    OrderType,
)


class TradingMode(str, Enum):
    """Supported ArbiX trading modes."""

    PAPER = "paper"
    LIVE = "live"


class ExecutionError(Exception):
    """Base exception for execution-related errors."""


class ExecutionRejectedError(ExecutionError):
    """Raised when an order is rejected before execution."""


class ExecutionConnectionError(ExecutionError):
    """Raised when communication with an exchange fails."""


@dataclass(frozen=True)
class ExecutionResult:
    """
    Result returned after an execution request.

    This provides a consistent result regardless of whether the
    underlying implementation is paper trading or live trading.
    """

    success: bool
    order_id: str
    exchange_order_id: str | None

    status: OrderStatus

    filled_quantity: Decimal
    average_fill_price: Decimal

    message: str = ""


class ExchangeExecutor(ABC):
    """
    Abstract exchange execution interface.

    Concrete exchange adapters implement this interface.

    The execution engine does not need to know how an exchange's
    REST API works.
    """

    @abstractmethod
    async def submit_order(
        self,
        order: Order,
    ) -> ExecutionResult:
        """
        Submit an order to the exchange.
        """

    @abstractmethod
    async def cancel_order(
        self,
        order: Order,
    ) -> ExecutionResult:
        """
        Cancel an existing exchange order.
        """

    @abstractmethod
    async def get_order(
        self,
        order: Order,
    ) -> ExecutionResult:
        """
        Retrieve the latest exchange state for an order.
        """


class PaperExchangeExecutor(ExchangeExecutor):
    """
    Simulated exchange executor.

    Paper mode never sends orders to a real exchange.

    This implementation is intentionally simple. Later, the paper
    trading engine can be connected to real order-book data to simulate
    realistic fills and slippage.
    """

    def __init__(
        self,
        simulated_price: Decimal | None = None,
    ) -> None:
        self.simulated_price = simulated_price

    async def submit_order(
        self,
        order: Order,
    ) -> ExecutionResult:
        """Simulate immediate order execution."""

        if order.quantity <= 0:
            raise ExecutionRejectedError(
                "Order quantity must be greater than zero."
            )

        if order.order_type == OrderType.LIMIT:
            if order.price is None:
                raise ExecutionRejectedError(
                    "Limit orders require a price."
                )

        execution_price = (
            order.price
            or self.simulated_price
        )

        if execution_price is None:
            raise ExecutionRejectedError(
                "No simulated execution price is available."
            )

        return ExecutionResult(
            success=True,
            order_id=order.order_id,
            exchange_order_id=f"PAPER-{order.order_id}",
            status=OrderStatus.FILLED,
            filled_quantity=order.quantity,
            average_fill_price=execution_price,
            message="Paper order executed successfully.",
        )

    async def cancel_order(
        self,
        order: Order,
    ) -> ExecutionResult:
        """Simulate order cancellation."""

        if order.is_terminal:
            return ExecutionResult(
                success=False,
                order_id=order.order_id,
                exchange_order_id=order.exchange_order_id,
                status=order.status,
                filled_quantity=order.filled_quantity,
                average_fill_price=order.average_fill_price,
                message="Order is already in a terminal state.",
            )

        return ExecutionResult(
            success=True,
            order_id=order.order_id,
            exchange_order_id=order.exchange_order_id,
            status=OrderStatus.CANCELLED,
            filled_quantity=order.filled_quantity,
            average_fill_price=order.average_fill_price,
            message="Paper order cancelled.",
        )

    async def get_order(
        self,
        order: Order,
    ) -> ExecutionResult:
        """Return the locally simulated order state."""

        return ExecutionResult(
            success=True,
            order_id=order.order_id,
            exchange_order_id=order.exchange_order_id,
            status=order.status,
            filled_quantity=order.filled_quantity,
            average_fill_price=order.average_fill_price,
            message="Paper order state retrieved.",
        )


class ExecutionEngine:
    """
    Coordinates order submission and state updates.

    Responsibilities:
        - Validate execution requests.
        - Create local orders.
        - Delegate exchange communication.
        - Update OrderManager.
        - Return normalized execution results.

    Responsibilities explicitly excluded:
        - Arbitrage detection.
        - Profitability calculation.
        - Risk evaluation.
        - Exchange-specific API implementation.
    """

    def __init__(
        self,
        order_manager: OrderManager,
        paper_executor: ExchangeExecutor | None = None,
        live_executors: dict[str, ExchangeExecutor] | None = None,
        trading_mode: TradingMode = TradingMode.PAPER,
    ) -> None:
        self.order_manager = order_manager

        self.paper_executor = (
            paper_executor
            or PaperExchangeExecutor()
        )

        self.live_executors = live_executors or {}

        self.trading_mode = trading_mode

    def register_live_executor(
        self,
        exchange: str,
        executor: ExchangeExecutor,
    ) -> None:
        """
        Register a live exchange executor.

        Example:

            engine.register_live_executor(
                "binance",
                BinanceExecutor(...)
            )
        """

        if not exchange:
            raise ValueError(
                "Exchange name cannot be empty."
            )

        self.live_executors[exchange] = executor

    async def submit_order(
        self,
        exchange: str,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        price: Decimal | None = None,
    ) -> ExecutionResult:
        """
        Create and submit an order.

        In PAPER mode the order is simulated.

        In LIVE mode an exchange-specific executor must be registered.
        """

        if not exchange:
            raise ValueError(
                "Exchange name cannot be empty."
            )

        if quantity <= 0:
            raise ExecutionRejectedError(
                "Order quantity must be greater than zero."
            )

        if order_type == OrderType.LIMIT and price is None:
            raise ExecutionRejectedError(
                "Limit orders require a price."
            )

        order = self.order_manager.create_order(
            exchange=exchange,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )

        executor = self._get_executor(exchange)

        try:
            result = await executor.submit_order(order)

        except ExecutionError:
            order.mark_failed()
            raise

        except Exception as error:
            order.mark_failed()

            raise ExecutionConnectionError(
                f"Execution failed on {exchange}."
            ) from error

        self._apply_execution_result(
            order=order,
            result=result,
        )

        return result

    async def cancel_order(
        self,
        order_id: str,
    ) -> ExecutionResult:
        """Cancel an existing order."""

        order = self.order_manager.get_required_order(
            order_id
        )

        if order.is_terminal:
            return ExecutionResult(
                success=False,
                order_id=order.order_id,
                exchange_order_id=order.exchange_order_id,
                status=order.status,
                filled_quantity=order.filled_quantity,
                average_fill_price=order.average_fill_price,
                message="Order is already terminal.",
            )

        self.order_manager.mark_cancel_requested(
            order_id
        )

        executor = self._get_executor(
            order.exchange
        )

        try:
            result = await executor.cancel_order(
                order
            )

        except Exception as error:
            order.mark_failed()

            raise ExecutionConnectionError(
                f"Failed to cancel order "
                f"{order_id}."
            ) from error

        self._apply_execution_result(
            order=order,
            result=result,
        )

        return result

    async def refresh_order(
        self,
        order_id: str,
    ) -> ExecutionResult:
        """
        Retrieve the latest exchange state for an order.
        """

        order = self.order_manager.get_required_order(
            order_id
        )

        executor = self._get_executor(
            order.exchange
        )

        try:
            result = await executor.get_order(
                order
            )

        except Exception as error:
            raise ExecutionConnectionError(
                f"Failed to retrieve order "
                f"{order_id}."
            ) from error

        self._apply_execution_result(
            order=order,
            result=result,
        )

        return result

    def _get_executor(
        self,
        exchange: str,
    ) -> ExchangeExecutor:
        """Return the appropriate executor for the trading mode."""

        if self.trading_mode == TradingMode.PAPER:
            return self.paper_executor

        executor = self.live_executors.get(exchange)

        if executor is None:
            raise ExecutionConnectionError(
                f"No live executor registered for "
                f"exchange: {exchange}"
            )

        return executor

    def _apply_execution_result(
        self,
        order: Order,
        result: ExecutionResult,
    ) -> None:
        """Synchronize OrderManager state with an execution result."""

        if result.exchange_order_id:
            if order.exchange_order_id is None:
                self.order_manager.mark_submitted(
                    order_id=order.order_id,
                    exchange_order_id=result.exchange_order_id,
                )

        self.order_manager.update_fill(
            order_id=order.order_id,
            filled_quantity=result.filled_quantity,
            average_fill_price=result.average_fill_price,
        )

        if result.status == OrderStatus.CANCELLED:
            self.order_manager.mark_cancelled(
                order_id=order.order_id
            )

        elif result.status == OrderStatus.REJECTED:
            self.order_manager.mark_rejected(
                order_id=order.order_id
            )

        elif result.status == OrderStatus.FAILED:
            self.order_manager.mark_failed(
                order_id=order.order_id
            )

        elif result.status == OrderStatus.EXPIRED:
            self.order_manager.mark_expired(
                order_id=order.order_id
            )