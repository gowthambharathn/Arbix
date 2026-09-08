"""
ArbiX Paper Trading Execution Engine

Simulates order execution for arbitrage opportunities using paper balances.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional

from arbitrage.calculator import ProfitabilityResult
from arbitrage.opportunity import ArbitrageOpportunity
from config.settings import settings

logger = logging.getLogger("ArbiX.PaperEngine")


@dataclass
class PaperTradeRecord:
    """Record of a simulated paper arbitrage trade."""

    opportunity: ArbitrageOpportunity
    result: ProfitabilityResult
    executed_buy_cost: Decimal
    executed_sell_revenue: Decimal
    net_profit: Decimal
    timestamp_ms: Optional[int] = None


class PaperEngine:
    """
    Paper trading engine that simulates real-time cross-exchange execution
    and updates balance accounts.
    """

    def __init__(self, initial_usdt_balance: Optional[Decimal] = None) -> None:
        balance = (
            initial_usdt_balance
            if initial_usdt_balance is not None
            else Decimal(str(settings.paper_balance_usdt))
        )
        self.usdt_balance: Decimal = balance
        self.trade_history: List[PaperTradeRecord] = []
        self.total_profit: Decimal = Decimal("0")

    def execute_arbitrage(
        self,
        opportunity: ArbitrageOpportunity,
        result: ProfitabilityResult,
    ) -> Optional[PaperTradeRecord]:
        """
        Simulate an arbitrage execution across the buy and sell venues.
        """
        total_required_usdt = result.buying_cost + result.buy_fee

        if total_required_usdt > self.usdt_balance:
            logger.warning(
                f"Insufficient paper USDT balance: Required {total_required_usdt:.2f}, "
                f"Available {self.usdt_balance:.2f}."
            )
            return None

        # Execute simulated buy & sell
        self.usdt_balance -= total_required_usdt
        gross_sell_revenue = result.selling_value - result.sell_fee
        self.usdt_balance += gross_sell_revenue

        net_profit = result.net_profit
        self.total_profit += net_profit

        record = PaperTradeRecord(
            opportunity=opportunity,
            result=result,
            executed_buy_cost=total_required_usdt,
            executed_sell_revenue=gross_sell_revenue,
            net_profit=net_profit,
        )
        self.trade_history.append(record)

        logger.info(
            f"Paper Trade Executed | Pair: {opportunity.symbol} | "
            f"Buy Exchange: {opportunity.buy_exchange} | Sell Exchange: {opportunity.sell_exchange} | "
            f"Net Profit: ${net_profit:.4f} ({result.net_profit_percentage:.2f}%) | "
            f"New USDT Balance: ${self.usdt_balance:.2f}"
        )
        return record

    def get_performance_summary(self) -> Dict[str, Decimal | int]:
        """Return aggregate execution statistics."""
        return {
            "total_trades": len(self.trade_history),
            "usdt_balance": self.usdt_balance,
            "total_net_profit": self.total_profit,
        }