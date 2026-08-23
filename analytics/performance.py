"""
ArbiX Performance Analytics

Builds higher-level trading performance reports from completed trade
results and portfolio equity data.

This module does not:
    - Execute trades
    - Communicate with exchanges
    - Modify positions
    - Store data permanently
    - Generate charts

It consumes trading data and produces analytical results.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from analytics.metrics import (
    TradeMetrics,
    calculate_max_drawdown,
    calculate_max_drawdown_percentage,
    calculate_profit_factor,
    calculate_return_percentage,
    calculate_trade_metrics,
)


@dataclass(frozen=True)
class PerformanceReport:
    """
    Complete performance report for an ArbiX trading period.
    """

    metrics: TradeMetrics

    profit_factor: Decimal

    starting_capital: Decimal
    ending_capital: Decimal

    net_return: Decimal
    return_percentage: Decimal

    maximum_drawdown: Decimal
    maximum_drawdown_percentage: Decimal

    total_trades: int
    profitable_trades: int
    losing_trades: int

    best_trade: Decimal
    worst_trade: Decimal


class PerformanceAnalyzer:
    """
    Generates performance reports from completed trades.

    The analyzer is stateless. Each call to generate_report() produces
    a new immutable PerformanceReport.
    """

    def generate_report(
        self,
        profits: list[Decimal],
        starting_capital: Decimal,
        equity_curve: list[Decimal] | None = None,
        trading_fees: Decimal = Decimal("0"),
        slippage: Decimal = Decimal("0"),
        execution_costs: Decimal = Decimal("0"),
    ) -> PerformanceReport:
        """
        Generate a complete trading performance report.

        Args:
            profits:
                Net P&L of each completed trade.

            starting_capital:
                Capital available at the beginning of the period.

            equity_curve:
                Historical portfolio equity values.

            trading_fees:
                Total trading fees.

            slippage:
                Total slippage cost.

            execution_costs:
                Other execution-related costs.

        Returns:
            PerformanceReport containing aggregate performance data.
        """

        if starting_capital <= 0:
            raise ValueError(
                "Starting capital must be greater than zero."
            )

        metrics = calculate_trade_metrics(
            profits=profits,
            trading_fees=trading_fees,
            slippage=slippage,
            execution_costs=execution_costs,
        )

        profit_factor = calculate_profit_factor(
            profits
        )

        net_return = metrics.net_profit

        ending_capital = (
            starting_capital
            + net_return
        )

        return_percentage = calculate_return_percentage(
            profit=net_return,
            capital=starting_capital,
        )

        if equity_curve:
            maximum_drawdown = calculate_max_drawdown(
                equity_curve
            )

            maximum_drawdown_percentage = (
                calculate_max_drawdown_percentage(
                    equity_curve
                )
            )

        else:
            maximum_drawdown = Decimal("0")
            maximum_drawdown_percentage = Decimal("0")

        return PerformanceReport(
            metrics=metrics,
            profit_factor=profit_factor,
            starting_capital=starting_capital,
            ending_capital=ending_capital,
            net_return=net_return,
            return_percentage=return_percentage,
            maximum_drawdown=maximum_drawdown,
            maximum_drawdown_percentage=(
                maximum_drawdown_percentage
            ),
            total_trades=metrics.total_trades,
            profitable_trades=metrics.winning_trades,
            losing_trades=metrics.losing_trades,
            best_trade=metrics.largest_profit,
            worst_trade=metrics.largest_loss,
        )


def calculate_equity_curve(
    starting_capital: Decimal,
    profits: list[Decimal],
) -> list[Decimal]:
    """
    Build an equity curve from starting capital and trade P&L.

    Example:

        Starting capital = 1000

        Profits:
            +50
            -20
            +30

        Equity curve:
            1000
            1050
            1030
            1060
    """

    if starting_capital <= 0:
        raise ValueError(
            "Starting capital must be greater than zero."
        )

    equity_curve = [
        starting_capital
    ]

    current_equity = starting_capital

    for profit in profits:
        current_equity += profit
        equity_curve.append(current_equity)

    return equity_curve


def calculate_sharpe_ratio(
    returns: list[Decimal],
    risk_free_rate: Decimal = Decimal("0"),
) -> Decimal:
    """
    Calculate a simplified Sharpe ratio.

    Formula:

        Sharpe Ratio =
            Average Excess Return
            / Standard Deviation of Returns

    This implementation uses trade-level returns.

    A production implementation may later use time-normalized
    returns such as hourly, daily, or minute-level returns.
    """

    if not returns:
        return Decimal("0")

    excess_returns = [
        value - risk_free_rate
        for value in returns
    ]

    mean_return = (
        sum(excess_returns, Decimal("0"))
        / Decimal(len(excess_returns))
    )

    if len(excess_returns) == 1:
        return Decimal("0")

    variance = (
        sum(
            (
                value - mean_return
            ) ** 2
            for value in excess_returns
        )
        / Decimal(len(excess_returns))
    )

    if variance <= 0:
        return Decimal("0")

    standard_deviation = _decimal_sqrt(
        variance
    )

    if standard_deviation == 0:
        return Decimal("0")

    return (
        mean_return
        / standard_deviation
    )


def calculate_average_trade_return(
    profits: list[Decimal],
    capital: Decimal,
) -> Decimal:
    """
    Calculate average trade return as a percentage of capital.
    """

    if capital <= 0:
        raise ValueError(
            "Capital must be greater than zero."
        )

    if not profits:
        return Decimal("0")

    total_profit = sum(
        profits,
        Decimal("0"),
    )

    return (
        total_profit
        / Decimal(len(profits))
        / capital
        * Decimal("100")
    )


def format_performance_report(
    report: PerformanceReport,
) -> str:
    """
    Convert a performance report into a human-readable text report.

    This is intended for console output and debugging.
    """

    metrics = report.metrics

    return (
        "\n"
        "========== ArbiX Performance Report ==========\n"
        f"Total Trades:              {metrics.total_trades}\n"
        f"Profitable Trades:         {metrics.winning_trades}\n"
        f"Losing Trades:             {metrics.losing_trades}\n"
        f"Breakeven Trades:          {metrics.breakeven_trades}\n"
        f"Win Rate:                  "
        f"{metrics.win_rate_percentage:.2f}%\n"
        f"Total Profit:              {metrics.total_profit}\n"
        f"Total Loss:                {metrics.total_loss}\n"
        f"Net Profit:                {metrics.net_profit}\n"
        f"Profit Factor:             {report.profit_factor}\n"
        f"Starting Capital:          "
        f"{report.starting_capital}\n"
        f"Ending Capital:            "
        f"{report.ending_capital}\n"
        f"Return:                    "
        f"{report.return_percentage:.2f}%\n"
        f"Maximum Drawdown:          "
        f"{report.maximum_drawdown}\n"
        f"Maximum Drawdown:          "
        f"{report.maximum_drawdown_percentage:.2f}%\n"
        f"Average Profit:            "
        f"{metrics.average_profit}\n"
        f"Average Loss:              "
        f"{metrics.average_loss}\n"
        f"Best Trade:                "
        f"{report.best_trade}\n"
        f"Worst Trade:               "
        f"{report.worst_trade}\n"
        f"Trading Fees:              "
        f"{metrics.total_trading_fees}\n"
        f"Slippage:                  "
        f"{metrics.total_slippage}\n"
        f"Execution Costs:           "
        f"{metrics.total_execution_costs}\n"
        "==============================================\n"
    )


def _decimal_sqrt(value: Decimal) -> Decimal:
    """
    Calculate the square root of a Decimal.

    Uses Decimal's native sqrt implementation.
    """

    if value < 0:
        raise ValueError(
            "Cannot calculate square root of a negative value."
        )

    return value.sqrt()