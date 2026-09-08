"""
ArbiX Profitability Calculator

Calculates the estimated profitability of cross-exchange arbitrage
opportunities using order-book liquidity and execution costs.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from config.settings import settings
from market_data.order_book import OrderBook
from arbitrage.opportunity import ArbitrageOpportunity


@dataclass(frozen=True)
class ProfitabilityResult:
    """Represents the estimated financial outcome of an arbitrage trade."""

    quantity: Decimal

    buying_cost: Decimal
    selling_value: Decimal

    buy_fee: Decimal
    sell_fee: Decimal

    buy_slippage: Decimal
    sell_slippage: Decimal

    transfer_cost: Decimal
    other_costs: Decimal

    gross_profit: Decimal
    total_costs: Decimal
    net_profit: Decimal

    net_profit_percentage: Decimal

    is_profitable: bool


class ProfitabilityCalculationError(Exception):
    """Base exception for profitability calculation errors."""


class InsufficientLiquidityError(ProfitabilityCalculationError):
    """Raised when an order book cannot satisfy the requested quantity."""


class ProfitabilityCalculator:
    """
    Calculates the estimated net profitability of an arbitrage trade.
    """

    def __init__(
        self,
        transfer_cost: Optional[Decimal] = None,
        other_costs: Optional[Decimal] = None,
        min_profit_percentage: Optional[Decimal] = None,
    ) -> None:
        self.transfer_cost = transfer_cost if transfer_cost is not None else Decimal("0")
        self.other_costs = other_costs if other_costs is not None else Decimal("0")
        self.min_profit_percentage = (
            min_profit_percentage
            if min_profit_percentage is not None
            else Decimal(str(settings.min_profit_percentage))
        )

        if self.transfer_cost < 0:
            raise ValueError("Transfer cost cannot be negative.")

        if self.other_costs < 0:
            raise ValueError("Other costs cannot be negative.")

    def calculate(
        self,
        opportunity: ArbitrageOpportunity,
        buy_order_book: OrderBook,
        sell_order_book: OrderBook,
        quantity: Optional[Decimal] = None,
        buy_fee_rate: Optional[Decimal] = None,
        sell_fee_rate: Optional[Decimal] = None,
    ) -> ProfitabilityResult:
        """Calculate estimated arbitrage profitability using system settings default overrides."""

        trade_qty = quantity if quantity is not None else Decimal(str(settings.max_trade_amount))
        buy_fee = buy_fee_rate if buy_fee_rate is not None else Decimal(str(settings.taker_fee))
        sell_fee = sell_fee_rate if sell_fee_rate is not None else Decimal(str(settings.taker_fee))

        self._validate_inputs(
            opportunity=opportunity,
            buy_order_book=buy_order_book,
            sell_order_book=sell_order_book,
            quantity=trade_qty,
            buy_fee_rate=buy_fee,
            sell_fee_rate=sell_fee,
        )

        buying_cost = self._calculate_buying_cost(
            order_book=buy_order_book,
            quantity=trade_qty,
        )

        selling_value = self._calculate_selling_value(
            order_book=sell_order_book,
            quantity=trade_qty,
        )

        buy_reference_cost = opportunity.buy_price * trade_qty
        sell_reference_value = opportunity.sell_price * trade_qty

        buy_slippage = max(
            Decimal("0"),
            buying_cost - buy_reference_cost,
        )

        sell_slippage = max(
            Decimal("0"),
            sell_reference_value - selling_value,
        )

        calculated_buy_fee = buying_cost * buy_fee
        calculated_sell_fee = selling_value * sell_fee

        gross_profit = selling_value - buying_cost

        total_costs = (
            calculated_buy_fee
            + calculated_sell_fee
            + buy_slippage
            + sell_slippage
            + self.transfer_cost
            + self.other_costs
        )

        net_profit = gross_profit - (
            calculated_buy_fee
            + calculated_sell_fee
            + self.transfer_cost
            + self.other_costs
        )

        total_investment = buying_cost + calculated_buy_fee

        if total_investment > 0:
            net_profit_percentage = (
                net_profit / total_investment * Decimal("100")
            )
        else:
            net_profit_percentage = Decimal("0")

        is_profitable = (
            net_profit > 0 and net_profit_percentage >= self.min_profit_percentage
        )

        return ProfitabilityResult(
            quantity=trade_qty,
            buying_cost=buying_cost,
            selling_value=selling_value,
            buy_fee=calculated_buy_fee,
            sell_fee=calculated_sell_fee,
            buy_slippage=buy_slippage,
            sell_slippage=sell_slippage,
            transfer_cost=self.transfer_cost,
            other_costs=self.other_costs,
            gross_profit=gross_profit,
            total_costs=total_costs,
            net_profit=net_profit,
            net_profit_percentage=net_profit_percentage,
            is_profitable=is_profitable,
        )

    @staticmethod
    def _calculate_buying_cost(
        order_book: OrderBook,
        quantity: Decimal,
    ) -> Decimal:
        try:
            return order_book.ask_cost(quantity)
        except ValueError as error:
            raise InsufficientLiquidityError(
                f"Insufficient ask liquidity for "
                f"{quantity} {order_book.base_asset}."
            ) from error

    @staticmethod
    def _calculate_selling_value(
        order_book: OrderBook,
        quantity: Decimal,
    ) -> Decimal:
        try:
            return order_book.bid_proceeds(quantity)
        except ValueError as error:
            raise InsufficientLiquidityError(
                f"Insufficient bid liquidity for "
                f"{quantity} {order_book.base_asset}."
            ) from error

    @staticmethod
    def _validate_inputs(
        opportunity: ArbitrageOpportunity,
        buy_order_book: OrderBook,
        sell_order_book: OrderBook,
        quantity: Decimal,
        buy_fee_rate: Decimal,
        sell_fee_rate: Decimal,
    ) -> None:
        if quantity <= 0:
            raise ValueError("Trade quantity must be greater than zero.")

        if buy_fee_rate < 0:
            raise ValueError("Buy fee rate cannot be negative.")

        if sell_fee_rate < 0:
            raise ValueError("Sell fee rate cannot be negative.")

        if buy_order_book.symbol != opportunity.symbol:
            raise ProfitabilityCalculationError(
                "Buy order-book symbol does not match opportunity."
            )

        if sell_order_book.symbol != opportunity.symbol:
            raise ProfitabilityCalculationError(
                "Sell order-book symbol does not match opportunity."
            )

        if buy_order_book.base_asset != sell_order_book.base_asset:
            raise ProfitabilityCalculationError(
                "Buy and sell order books use different base assets."
            )

        if buy_order_book.quote_asset != sell_order_book.quote_asset:
            raise ProfitabilityCalculationError(
                "Buy and sell order books use different quote assets."
            )