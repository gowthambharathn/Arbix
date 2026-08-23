"""
ArbiX Risk Manager

Evaluates arbitrage opportunities against configured risk limits.

The risk manager does not execute orders. It only determines whether
an opportunity is allowed to proceed to the execution layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from arbitrage.calculator import ProfitabilityResult
from arbitrage.opportunity import ArbitrageOpportunity
from market_data.order_book import OrderBook
from risk.limits import RiskLimits


class RiskDecision(str, Enum):
    """Possible decisions produced by the risk manager."""

    APPROVED = "approved"
    REJECTED = "rejected"


class RiskRejectionReason(str, Enum):
    """Reasons why an opportunity can be rejected."""

    TRADE_SIZE_EXCEEDED = "trade_size_exceeded"
    CAPITAL_EXPOSURE_EXCEEDED = "capital_exposure_exceeded"
    PROFIT_BELOW_THRESHOLD = "profit_below_threshold"
    SLIPPAGE_TOO_HIGH = "slippage_too_high"
    INSUFFICIENT_LIQUIDITY = "insufficient_liquidity"
    DAILY_LOSS_LIMIT_REACHED = "daily_loss_limit_reached"
    MARKET_DATA_STALE = "market_data_stale"
    OPPORTUNITY_EXPIRED = "opportunity_expired"
    INVALID_PROFITABILITY = "invalid_profitability"
    TRADING_HALTED = "trading_halted"


@dataclass(frozen=True)
class RiskCheckResult:
    """Result of a risk evaluation."""

    decision: RiskDecision
    reasons: tuple[RiskRejectionReason, ...]

    @property
    def approved(self) -> bool:
        """Return True when the opportunity is approved."""

        return self.decision == RiskDecision.APPROVED


class RiskManager:
    """
    Evaluates opportunities against configured risk limits.

    The manager is intentionally stateless with respect to individual
    trades. Daily loss and exposure state can be supplied through the
    evaluation method.
    """

    def __init__(self, limits: RiskLimits) -> None:
        self.limits = limits
        self._trading_halted = False

    @property
    def trading_halted(self) -> bool:
        """Return whether trading has been manually halted."""

        return self._trading_halted

    def halt_trading(self) -> None:
        """Immediately prevent new trades from being approved."""

        self._trading_halted = True

    def resume_trading(self) -> None:
        """
        Resume trading after a manual or emergency halt.

        This should only be called after the cause of the halt has
        been investigated and resolved.
        """

        self._trading_halted = False

    def evaluate(
        self,
        opportunity: ArbitrageOpportunity,
        profitability: ProfitabilityResult,
        quantity: Decimal,
        current_capital_exposure: Decimal,
        daily_loss: Decimal,
        buy_order_book: OrderBook,
        sell_order_book: OrderBook,
    ) -> RiskCheckResult:
        """
        Evaluate an arbitrage opportunity against all risk limits.

        Args:
            opportunity:
                Detected arbitrage opportunity.

            profitability:
                Result produced by the profitability calculator.

            quantity:
                Intended base-asset trade quantity.

            current_capital_exposure:
                Capital currently committed to active positions/orders.

            daily_loss:
                Current realized loss for the trading day.

            buy_order_book:
                Current order book for the buy exchange.

            sell_order_book:
                Current order book for the sell exchange.

        Returns:
            Structured risk decision.
        """

        reasons: list[RiskRejectionReason] = []

        if self._trading_halted:
            reasons.append(
                RiskRejectionReason.TRADING_HALTED
            )

        if quantity <= 0:
            reasons.append(
                RiskRejectionReason.TRADE_SIZE_EXCEEDED
            )
        elif quantity > self.limits.max_trade_amount:
            reasons.append(
                RiskRejectionReason.TRADE_SIZE_EXCEEDED
            )

        trade_value = profitability.buying_cost + profitability.buy_fee

        if (
            current_capital_exposure + trade_value
            > self.limits.max_capital_exposure
        ):
            reasons.append(
                RiskRejectionReason.CAPITAL_EXPOSURE_EXCEEDED
            )

        if (
            profitability.net_profit_percentage
            < self.limits.min_profit_percentage
        ):
            reasons.append(
                RiskRejectionReason.PROFIT_BELOW_THRESHOLD
            )

        total_slippage = self._calculate_slippage_percentage(
            profitability=profitability,
        )

        if total_slippage > self.limits.max_slippage_percentage:
            reasons.append(
                RiskRejectionReason.SLIPPAGE_TOO_HIGH
            )

        if not self._has_sufficient_liquidity(
            quantity=quantity,
            order_book=buy_order_book,
        ):
            reasons.append(
                RiskRejectionReason.INSUFFICIENT_LIQUIDITY
            )

        if not self._has_sufficient_liquidity(
            quantity=quantity,
            order_book=sell_order_book,
        ):
            reasons.append(
                RiskRejectionReason.INSUFFICIENT_LIQUIDITY
            )

        if daily_loss >= self.limits.max_daily_loss:
            reasons.append(
                RiskRejectionReason.DAILY_LOSS_LIMIT_REACHED
            )

        if profitability.net_profit.is_nan():
            reasons.append(
                RiskRejectionReason.INVALID_PROFITABILITY
            )

        if opportunity.is_expired(
            self.limits.max_market_data_age_seconds
        ):
            reasons.append(
                RiskRejectionReason.OPPORTUNITY_EXPIRED
            )

        if reasons:
            return RiskCheckResult(
                decision=RiskDecision.REJECTED,
                reasons=tuple(dict.fromkeys(reasons)),
            )

        return RiskCheckResult(
            decision=RiskDecision.APPROVED,
            reasons=(),
        )

    def _calculate_slippage_percentage(
        self,
        profitability: ProfitabilityResult,
    ) -> Decimal:
        """
        Calculate total slippage as a percentage of the buying cost.
        """

        total_slippage = (
            profitability.buy_slippage
            + profitability.sell_slippage
        )

        if profitability.buying_cost <= 0:
            return Decimal("0")

        return (
            total_slippage
            / profitability.buying_cost
            * Decimal("100")
        )

    @staticmethod
    def _has_sufficient_liquidity(
        quantity: Decimal,
        order_book: OrderBook,
    ) -> bool:
        """
        Verify that the requested quantity can be executed.

        The actual profitability calculator already performs a more
        detailed liquidity calculation. This check exists as an
        additional safety gate before execution.
        """

        if quantity <= 0:
            return False

        try:
            if order_book.bids:
                order_book.bid_proceeds(quantity)
            else:
                return False

            if order_book.asks:
                order_book.ask_cost(quantity)
            else:
                return False

        except ValueError:
            return False

        return True