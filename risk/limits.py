"""
ArbiX Risk Limits

Defines configurable risk limits used by the ArbiX risk-management
system.

This module contains risk configuration only. Enforcement belongs to
the risk manager.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RiskLimits:
    """
    Defines the maximum risk ArbiX is allowed to take.

    All monetary values are expressed in the configured quote currency.

    Example:
        max_trade_amount = 100
        max_capital_exposure = 500
    """

    max_trade_amount: Decimal
    max_capital_exposure: Decimal

    min_profit_percentage: Decimal
    max_slippage_percentage: Decimal

    min_liquidity_ratio: Decimal

    max_daily_loss: Decimal

    max_order_timeout_seconds: float
    max_market_data_age_seconds: float

    def __post_init__(self) -> None:
        """Validate all configured risk limits."""

        if self.max_trade_amount <= 0:
            raise ValueError(
                "max_trade_amount must be greater than zero."
            )

        if self.max_capital_exposure <= 0:
            raise ValueError(
                "max_capital_exposure must be greater than zero."
            )

        if self.max_trade_amount > self.max_capital_exposure:
            raise ValueError(
                "max_trade_amount cannot exceed "
                "max_capital_exposure."
            )

        if self.min_profit_percentage < 0:
            raise ValueError(
                "min_profit_percentage cannot be negative."
            )

        if self.max_slippage_percentage < 0:
            raise ValueError(
                "max_slippage_percentage cannot be negative."
            )

        if not (
            Decimal("0")
            <= self.min_liquidity_ratio
            <= Decimal("1")
        ):
            raise ValueError(
                "min_liquidity_ratio must be between 0 and 1."
            )

        if self.max_daily_loss <= 0:
            raise ValueError(
                "max_daily_loss must be greater than zero."
            )

        if self.max_order_timeout_seconds <= 0:
            raise ValueError(
                "max_order_timeout_seconds must be "
                "greater than zero."
            )

        if self.max_market_data_age_seconds <= 0:
            raise ValueError(
                "max_market_data_age_seconds must be "
                "greater than zero."
            )