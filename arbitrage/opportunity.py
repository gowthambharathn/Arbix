"""
ArbiX Arbitrage Opportunity Models

Defines the domain models used to represent cross-exchange
arbitrage opportunities.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum


class OpportunityStatus(str, Enum):
    """Lifecycle state of an arbitrage opportunity."""

    DETECTED = "detected"
    EVALUATED = "evaluated"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass(frozen=True)
class ArbitrageOpportunity:
    """
    Represents a cross-exchange arbitrage opportunity.

    An opportunity describes where an asset could theoretically be
    bought and sold, together with the prices observed at detection time.

    This model does not perform profitability calculations or execute
    orders. Those responsibilities belong to other components.
    """

    symbol: str

    buy_exchange: str
    sell_exchange: str

    buy_price: Decimal
    sell_price: Decimal

    detected_at: float

    status: OpportunityStatus = OpportunityStatus.DETECTED

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("Symbol cannot be empty.")

        if not self.buy_exchange:
            raise ValueError(
                "Buy exchange cannot be empty."
            )

        if not self.sell_exchange:
            raise ValueError(
                "Sell exchange cannot be empty."
            )

        if self.buy_exchange == self.sell_exchange:
            raise ValueError(
                "Buy and sell exchanges must be different."
            )

        if self.buy_price <= 0:
            raise ValueError(
                "Buy price must be greater than zero."
            )

        if self.sell_price <= 0:
            raise ValueError(
                "Sell price must be greater than zero."
            )

        if self.detected_at <= 0:
            raise ValueError(
                "Detection timestamp must be greater than zero."
            )

    @property
    def gross_spread(self) -> Decimal:
        """
        Return the absolute price difference.

        Example:

            Buy  = $100,000
            Sell = $100,300

            Gross spread = $300
        """

        return self.sell_price - self.buy_price

    @property
    def gross_spread_percentage(self) -> Decimal:
        """
        Return the gross spread as a percentage of the buy price.

        Example:

            Buy  = $100,000
            Sell = $100,300

            Spread = 0.30%
        """

        return (
            self.gross_spread
            / self.buy_price
            * Decimal("100")
        )

    @property
    def is_profitable_before_costs(self) -> bool:
        """
        Return whether the raw spread is positive.

        This is NOT an indication of actual profitability.

        Fees, slippage, liquidity, transfer costs, and other execution
        costs must still be deducted.
        """

        return self.gross_spread > 0

    @property
    def age_seconds(self) -> float:
        """Return the approximate age of the opportunity."""

        current_time = datetime.now(timezone.utc).timestamp()

        return max(
            0.0,
            current_time - self.detected_at,
        )

    def is_expired(self, max_age_seconds: float) -> bool:
        """
        Determine whether the opportunity is too old to execute.

        Args:
            max_age_seconds: Maximum acceptable opportunity age.

        Returns:
            True when the opportunity has exceeded the allowed age.
        """

        if max_age_seconds <= 0:
            raise ValueError(
                "max_age_seconds must be greater than zero."
            )

        return self.age_seconds > max_age_seconds