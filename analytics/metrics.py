"""
ArbiX Analytics Metrics

Provides reusable calculations for evaluating arbitrage and trading
performance.

This module contains pure metric calculations and does not perform:
    - Exchange communication
    - Order execution
    - Database operations
    - File logging
    - Plotting
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TradeMetrics:
    """
    Metrics calculated from a collection of completed trades.

    Monetary values are represented using Decimal to avoid unnecessary
    floating-point precision issues.
    """

    total_trades: int
    winning_trades: int
    losing_trades: int
    breakeven_trades: int

    total_profit: Decimal
    total_loss: Decimal
    net_profit: Decimal

    win_rate_percentage: Decimal
    average_profit: Decimal
    average_loss: Decimal

    largest_profit: Decimal
    largest_loss: Decimal

    total_trading_fees: Decimal
    total_slippage: Decimal
    total_execution_costs: Decimal


@dataclass(frozen=True)
class ProfitLoss:
    """
    Represents the profit and loss of a single completed trade.
    """

    gross_profit: Decimal
    trading_fees: Decimal
    slippage: Decimal
    transfer_costs: Decimal
    other_execution_costs: Decimal

    @property
    def net_profit(self) -> Decimal:
        """Return profit after all execution costs."""

        return (
            self.gross_profit
            - self.trading_fees
            - self.slippage
            - self.transfer_costs
            - self.other_execution_costs
        )


def calculate_net_profit(
    gross_profit: Decimal,
    trading_fees: Decimal = Decimal("0"),
    slippage: Decimal = Decimal("0"),
    transfer_costs: Decimal = Decimal("0"),
    other_execution_costs: Decimal = Decimal("0"),
) -> Decimal:
    """
    Calculate net profit after execution costs.

    Formula:

        Net Profit =
            Gross Profit
            - Trading Fees
            - Slippage
            - Transfer Costs
            - Other Execution Costs
    """

    _validate_non_negative(
        trading_fees=trading_fees,
        slippage=slippage,
        transfer_costs=transfer_costs,
        other_execution_costs=other_execution_costs,
    )

    return (
        gross_profit
        - trading_fees
        - slippage
        - transfer_costs
        - other_execution_costs
    )


def calculate_return_percentage(
    profit: Decimal,
    capital: Decimal,
) -> Decimal:
    """
    Calculate percentage return on capital.

    Example:

        profit = 10
        capital = 100

        return = 10%
    """

    if capital <= 0:
        raise ValueError(
            "Capital must be greater than zero."
        )

    return (
        profit
        / capital
        * Decimal("100")
    )


def calculate_win_rate(
    winning_trades: int,
    total_trades: int,
) -> Decimal:
    """
    Calculate the percentage of profitable trades.
    """

    if total_trades < 0:
        raise ValueError(
            "Total trades cannot be negative."
        )

    if winning_trades < 0:
        raise ValueError(
            "Winning trades cannot be negative."
        )

    if winning_trades > total_trades:
        raise ValueError(
            "Winning trades cannot exceed total trades."
        )

    if total_trades == 0:
        return Decimal("0")

    return (
        Decimal(winning_trades)
        / Decimal(total_trades)
        * Decimal("100")
    )


def calculate_average_profit(
    profits: list[Decimal],
) -> Decimal:
    """
    Calculate the average value of profitable trades.

    Non-positive values are ignored.
    """

    winning_profits = [
        profit
        for profit in profits
        if profit > 0
    ]

    if not winning_profits:
        return Decimal("0")

    return (
        sum(winning_profits, Decimal("0"))
        / Decimal(len(winning_profits))
    )


def calculate_average_loss(
    profits: list[Decimal],
) -> Decimal:
    """
    Calculate the average loss of losing trades.

    Returns a negative value when losses exist.
    """

    losing_profits = [
        profit
        for profit in profits
        if profit < 0
    ]

    if not losing_profits:
        return Decimal("0")

    return (
        sum(losing_profits, Decimal("0"))
        / Decimal(len(losing_profits))
    )


def calculate_profit_factor(
    profits: list[Decimal],
) -> Decimal:
    """
    Calculate profit factor.

    Formula:

        Profit Factor =
            Gross Winning Profit
            / Absolute Gross Losing Profit

    A value greater than 1 means gross profits exceed gross losses.

    Returns:
        Decimal("0") when no losses exist and no profits exist.
        Decimal("Infinity") when profits exist but there are no losses.
    """

    gross_profit = sum(
        (
            profit
            for profit in profits
            if profit > 0
        ),
        Decimal("0"),
    )

    gross_loss = abs(
        sum(
            (
                profit
                for profit in profits
                if profit < 0
            ),
            Decimal("0"),
        )
    )

    if gross_loss == 0:
        if gross_profit > 0:
            return Decimal("Infinity")

        return Decimal("0")

    return gross_profit / gross_loss


def calculate_max_drawdown(
    equity_curve: list[Decimal],
) -> Decimal:
    """
    Calculate maximum drawdown from an equity curve.

    The returned value is a positive monetary amount.

    Example:

        Equity:
            1000
            1100
            1050
            900

        Maximum drawdown:
            200
    """

    if not equity_curve:
        return Decimal("0")

    peak = equity_curve[0]
    max_drawdown = Decimal("0")

    for equity in equity_curve:
        if equity > peak:
            peak = equity

        drawdown = peak - equity

        if drawdown > max_drawdown:
            max_drawdown = drawdown

    return max_drawdown


def calculate_max_drawdown_percentage(
    equity_curve: list[Decimal],
) -> Decimal:
    """
    Calculate maximum drawdown as a percentage of the previous peak.

    Returns a positive percentage.
    """

    if not equity_curve:
        return Decimal("0")

    peak = equity_curve[0]
    max_drawdown_percentage = Decimal("0")

    for equity in equity_curve:
        if equity > peak:
            peak = equity

        if peak <= 0:
            continue

        drawdown_percentage = (
            (peak - equity)
            / peak
            * Decimal("100")
        )

        if drawdown_percentage > max_drawdown_percentage:
            max_drawdown_percentage = drawdown_percentage

    return max_drawdown_percentage


def calculate_trade_metrics(
    profits: list[Decimal],
    trading_fees: Decimal = Decimal("0"),
    slippage: Decimal = Decimal("0"),
    execution_costs: Decimal = Decimal("0"),
) -> TradeMetrics:
    """
    Calculate aggregate trading metrics.

    Args:
        profits:
            Net profit/loss for each completed trade.

        trading_fees:
            Total trading fees.

        slippage:
            Total slippage cost.

        execution_costs:
            Other execution-related costs.

    Returns:
        TradeMetrics containing aggregate performance information.
    """

    _validate_non_negative(
        trading_fees=trading_fees,
        slippage=slippage,
        execution_costs=execution_costs,
    )

    total_trades = len(profits)

    winning_trades = sum(
        1
        for profit in profits
        if profit > 0
    )

    losing_trades = sum(
        1
        for profit in profits
        if profit < 0
    )

    breakeven_trades = sum(
        1
        for profit in profits
        if profit == 0
    )

    total_profit = sum(
        (
            profit
            for profit in profits
            if profit > 0
        ),
        Decimal("0"),
    )

    total_loss = sum(
        (
            profit
            for profit in profits
            if profit < 0
        ),
        Decimal("0"),
    )

    net_profit = sum(
        profits,
        Decimal("0"),
    )

    average_profit = calculate_average_profit(
        profits
    )

    average_loss = calculate_average_loss(
        profits
    )

    largest_profit = max(
        profits,
        default=Decimal("0"),
    )

    largest_loss = min(
        profits,
        default=Decimal("0"),
    )

    return TradeMetrics(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        breakeven_trades=breakeven_trades,
        total_profit=total_profit,
        total_loss=total_loss,
        net_profit=net_profit,
        win_rate_percentage=calculate_win_rate(
            winning_trades=winning_trades,
            total_trades=total_trades,
        ),
        average_profit=average_profit,
        average_loss=average_loss,
        largest_profit=largest_profit,
        largest_loss=largest_loss,
        total_trading_fees=trading_fees,
        total_slippage=slippage,
        total_execution_costs=execution_costs,
    )


def _validate_non_negative(
    **values: Decimal,
) -> None:
    """Validate that cost values are not negative."""

    for name, value in values.items():
        if value < 0:
            raise ValueError(
                f"{name} cannot be negative."
            )