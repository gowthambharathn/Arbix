"""
ArbiX Arbitrage Opportunity Model
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class ArbitrageOpportunity:
    """Represents a potential arbitrage route between two exchanges."""

    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: Decimal
    sell_price: Decimal
    detected_at: float = field(default_factory=time.time)

    @property
    def gross_spread(self) -> Decimal:
        """Calculate the absolute price difference between venues."""
        return self.sell_price - self.buy_price

    @property
    def gross_spread_percentage(self) -> Decimal:
        """Calculate gross spread as a percentage of the purchase price."""
        if self.buy_price <= 0:
            return Decimal("0")
        return (self.gross_spread / self.buy_price) * Decimal("100")