"""
ArbiX Arbitrage Opportunity Finder

Scans order books across exchanges to identify profitable opportunities.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional
import time

from arbitrage.calculator import ProfitabilityCalculator, ProfitabilityResult
from arbitrage.opportunity import ArbitrageOpportunity
from market_data.order_book import OrderBook


class ArbitrageFinder:
    """
    Scans live order books across multiple exchanges to identify and rank
    profitable cross-exchange arbitrage opportunities.
    """

    def __init__(
        self,
        calculator: Optional[ProfitabilityCalculator] = None,
    ) -> None:
        self.calculator = calculator or ProfitabilityCalculator()

    def find_opportunities(
        self,
        order_books: Dict[str, OrderBook],
        trade_quantity: Optional[Decimal] = None,
    ) -> List[tuple[ArbitrageOpportunity, ProfitabilityResult]]:
        """
        Compare order books across exchanges for a target trading pair.

        Args:
            order_books: A dictionary mapping exchange names to their OrderBook objects.
            trade_quantity: Quantity to evaluate (uses settings default if None).

        Returns:
            A list of tuples containing detected opportunities paired with their profitability results,
            sorted by highest net profit percentage.
        """
        opportunities: List[tuple[ArbitrageOpportunity, ProfitabilityResult]] = []
        exchanges = list(order_books.keys())

        for i, buy_ex_name in enumerate(exchanges):
            for sell_ex_name in exchanges[i + 1:]:
                buy_book = order_books[buy_ex_name]
                sell_book = order_books[sell_ex_name]

                # Compare Exchange A -> Exchange B and Exchange B -> Exchange A
                for source_ex, target_ex, b_book, s_book in [
                    (buy_ex_name, sell_ex_name, buy_book, sell_book),
                    (sell_ex_name, buy_ex_name, sell_book, buy_book),
                ]:
                    if not b_book.asks or not s_book.bids:
                        continue

                    # Access the .price attribute directly on OrderBookLevel objects
                    buy_price = b_book.asks[0].price
                    sell_price = s_book.bids[0].price

                    # Raw spread check before full depth computation
                    if sell_price <= buy_price:
                        continue

                    # ... inside finder.py loop ...
                    opportunity = ArbitrageOpportunity(
                        symbol=b_book.symbol,
                        buy_exchange=source_ex,
                        sell_exchange=target_ex,
                        buy_price=buy_price,
                        sell_price=sell_price,
                        detected_at=time.time(),
                    )

                    try:
                        result = self.calculator.calculate(
                            opportunity=opportunity,
                            buy_order_book=b_book,
                            sell_order_book=s_book,
                            quantity=trade_quantity,
                        )

                        if result.is_profitable:
                            opportunities.append((opportunity, result))

                    except Exception:
                        continue

        # Sort opportunities by highest net profit percentage descending
        opportunities.sort(key=lambda item: item[1].net_profit_percentage, reverse=True)
        return opportunities