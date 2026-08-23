"""
ArbiX Arbitrage Detector

Detects potential cross-exchange arbitrage opportunities from
normalized market-price data.

This component identifies price differences only. It does not
calculate final profitability, perform risk checks, or execute orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from itertools import combinations
from time import time
from typing import Iterable

from arbitrage.opportunity import ArbitrageOpportunity
from market_data.price_feed import PriceTick


@dataclass(frozen=True)
class DetectionConfig:
    """Configuration controlling arbitrage opportunity detection."""

    min_spread_percentage: Decimal = Decimal("0")
    max_price_age_seconds: float = 5.0

    def __post_init__(self) -> None:
        if self.min_spread_percentage < 0:
            raise ValueError(
                "Minimum spread percentage cannot be negative."
            )

        if self.max_price_age_seconds <= 0:
            raise ValueError(
                "Maximum price age must be greater than zero."
            )


class ArbitrageDetector:
    """
    Detects cross-exchange arbitrage opportunities.

    For each trading pair, the detector compares:

        Exchange A ask
            against
        Exchange B bid

    The theoretical arbitrage direction is:

        BUY  -> exchange with lower ask
        SELL -> exchange with higher bid

    The detector does not determine whether the opportunity is
    actually profitable after fees, slippage, liquidity, or other
    execution costs.
    """

    def __init__(
        self,
        config: DetectionConfig | None = None,
    ) -> None:
        self.config = config or DetectionConfig()

    def detect(
        self,
        prices: Iterable[PriceTick],
    ) -> list[ArbitrageOpportunity]:
        """
        Detect cross-exchange arbitrage opportunities.

        Args:
            prices:
                Collection of normalized price ticks.

        Returns:
            List of detected arbitrage opportunities.
        """

        valid_prices = self._filter_valid_prices(prices)

        grouped_prices = self._group_by_symbol(valid_prices)

        opportunities: list[ArbitrageOpportunity] = []

        for symbol, symbol_prices in grouped_prices.items():
            if len(symbol_prices) < 2:
                continue

            opportunities.extend(
                self._detect_for_symbol(
                    symbol=symbol,
                    prices=symbol_prices,
                )
            )

        return opportunities

    def _detect_for_symbol(
        self,
        symbol: str,
        prices: list[PriceTick],
    ) -> list[ArbitrageOpportunity]:
        """Detect opportunities for one trading pair."""

        opportunities: list[ArbitrageOpportunity] = []

        for first, second in combinations(prices, 2):
            opportunity = self._compare_prices(
                symbol=symbol,
                first=first,
                second=second,
            )

            if opportunity is not None:
                opportunities.append(opportunity)

        return opportunities

    def _compare_prices(
        self,
        symbol: str,
        first: PriceTick,
        second: PriceTick,
    ) -> ArbitrageOpportunity | None:
        """
        Compare two exchange prices and determine the profitable direction.

        The comparison uses:

            Lower ask  -> BUY
            Higher bid -> SELL
        """

        if first.exchange == second.exchange:
            return None

        if first.symbol != symbol or second.symbol != symbol:
            return None

        if first.ask < second.bid:
            buy_price = first.ask
            sell_price = second.bid

            buy_exchange = first.exchange
            sell_exchange = second.exchange

        elif second.ask < first.bid:
            buy_price = second.ask
            sell_price = first.bid

            buy_exchange = second.exchange
            sell_exchange = first.exchange

        else:
            return None

        spread = sell_price - buy_price

        if buy_price <= 0:
            return None

        spread_percentage = (
            spread
            / buy_price
            * Decimal("100")
        )

        if (
            spread_percentage
            < self.config.min_spread_percentage
        ):
            return None

        return ArbitrageOpportunity(
            symbol=symbol,
            buy_exchange=buy_exchange,
            sell_exchange=sell_exchange,
            buy_price=buy_price,
            sell_price=sell_price,
            detected_at=max(
                first.timestamp,
                second.timestamp,
            ),
        )

    def _filter_valid_prices(
        self,
        prices: Iterable[PriceTick],
    ) -> list[PriceTick]:
        """Remove stale or invalid market data."""

        current_time = time()

        valid_prices: list[PriceTick] = []

        for price in prices:
            age = current_time - price.timestamp

            if age < 0:
                continue

            if age > self.config.max_price_age_seconds:
                continue

            valid_prices.append(price)

        return valid_prices

    @staticmethod
    def _group_by_symbol(
        prices: Iterable[PriceTick],
    ) -> dict[str, list[PriceTick]]:
        """Group price ticks by trading symbol."""

        grouped: dict[str, list[PriceTick]] = {}

        for price in prices:
            grouped.setdefault(
                price.symbol,
                [],
            ).append(price)

        return grouped