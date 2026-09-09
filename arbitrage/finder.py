"""
ArbiX Arbitrage Finder

Evaluates real-time order books across exchanges to find gross and net spread opportunities.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import config.settings as settings

logger = logging.getLogger("ArbiX.Finder")

# Resolve parameters safely from settings
MIN_PROFIT_PERCENTAGE = getattr(settings, "MIN_PROFIT_PERCENTAGE", getattr(settings, "MIN_PROFIT_THRESHOLD", 0.20))
TOTAL_TAKER_FEE_PERCENTAGE = getattr(settings, "TOTAL_TAKER_FEE_PERCENTAGE", getattr(settings, "TOTAL_FEE_PERCENTAGE", 0.20))


class ArbitrageOpportunity:
    """Represents an evaluated arbitrage opportunity."""

    def __init__(
        self,
        symbol: str,
        buy_exchange: str,
        sell_exchange: str,
        buy_price: float,
        sell_price: float,
        gross_spread: float,
        gross_spread_pct: float,
        net_spread_pct: float,
        is_profitable: bool,
    ) -> None:
        self.symbol = symbol
        self.buy_exchange = buy_exchange
        self.sell_exchange = sell_exchange
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.gross_spread = gross_spread
        self.gross_spread_pct = gross_spread_pct
        self.net_spread_pct = net_spread_pct
        self.is_profitable = is_profitable


def _extract_price(level: object) -> Optional[float]:
    """Extracts numeric price from an OrderBookLevel object, tuple, dict, or float."""
    if level is None:
        return None
    if isinstance(level, (int, float)):
        return float(level)
    if hasattr(level, "price"):
        return float(level.price)
    if isinstance(level, (list, tuple)) and len(level) > 0:
        return float(level[0])
    if isinstance(level, dict) and "price" in level:
        return float(level["price"])
    return None


def find_arbitrage_opportunities(
    order_books: Dict[Tuple[str, str], object],
    symbols: List[str],
    exchanges: List[str],
) -> List[ArbitrageOpportunity]:
    """
    Scans active order books to discover arbitrage spreads across specified exchanges.
    """
    opportunities: List[ArbitrageOpportunity] = []

    for symbol in symbols:
        for buy_ex in exchanges:
            for sell_ex in exchanges:
                if buy_ex == sell_ex:
                    continue

                buy_book = order_books.get((buy_ex, symbol))
                sell_book = order_books.get((sell_ex, symbol))

                if not buy_book or not sell_book:
                    continue

                best_ask_raw = getattr(buy_book, "best_ask", None)
                best_bid_raw = getattr(sell_book, "best_bid", None)

                best_ask = _extract_price(best_ask_raw)
                best_bid = _extract_price(best_bid_raw)

                if best_ask is None or best_bid is None or best_ask <= 0:
                    continue

                gross_spread = best_bid - best_ask
                gross_spread_pct = (gross_spread / best_ask) * 100.0
                net_spread_pct = gross_spread_pct - TOTAL_TAKER_FEE_PERCENTAGE

                is_profitable = net_spread_pct >= MIN_PROFIT_PERCENTAGE

                opp = ArbitrageOpportunity(
                    symbol=symbol,
                    buy_exchange=buy_ex,
                    sell_exchange=sell_ex,
                    buy_price=best_ask,
                    sell_price=best_bid,
                    gross_spread=gross_spread,
                    gross_spread_pct=gross_spread_pct,
                    net_spread_pct=net_spread_pct,
                    is_profitable=is_profitable,
                )
                opportunities.append(opp)

                if is_profitable:
                    logger.info(
                        f"🔥 [PROFITABLE OPP!] {symbol} | Buy {buy_ex} @ ${best_ask:.4f} "
                        f"-> Sell {sell_ex} @ ${best_bid:.4f} | Net Profit: {net_spread_pct:+.4f}%"
                    )

    return opportunities