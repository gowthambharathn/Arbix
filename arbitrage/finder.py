"""
ArbiX Arbitrage Finder

Evaluates real-time order books across exchanges to find
arbitrage opportunities using order-book depth, trading fees,
executable trade prices, order-book freshness, and liquidity.
"""

from __future__ import annotations

import logging
import time
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import config.settings as settings_module


logger = logging.getLogger("ArbiX.Finder")

settings = settings_module.settings

MIN_PROFIT_PERCENTAGE = Decimal(
    str(settings.min_profit_percentage)
)

TRADE_AMOUNT = Decimal(
    str(settings.max_trade_amount)
)

MAX_ORDER_BOOK_AGE_SECONDS = 5.0

MIN_LIQUIDITY_MULTIPLIER = Decimal("1.0")


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
        buy_fee: float,
        sell_fee: float,
        total_fee_pct: float,
        net_profit: float,
        net_spread_pct: float,
        trade_quantity: float,
        trade_amount: float,
        is_profitable: bool,
    ) -> None:
        self.symbol = symbol
        self.buy_exchange = buy_exchange
        self.sell_exchange = sell_exchange

        self.buy_price = buy_price
        self.sell_price = sell_price

        self.gross_spread = gross_spread
        self.gross_spread_pct = gross_spread_pct

        self.buy_fee = buy_fee
        self.sell_fee = sell_fee
        self.total_fee_pct = total_fee_pct

        self.net_profit = net_profit
        self.net_spread_pct = net_spread_pct

        self.trade_quantity = trade_quantity
        self.trade_amount = trade_amount

        self.is_profitable = is_profitable


def _calculate_execution(
    buy_book: object,
    sell_book: object,
    trade_amount: Decimal,
) -> Optional[
    Tuple[
        Decimal,
        Decimal,
        Decimal,
        Decimal,
        Decimal,
    ]
]:
    """
    Calculate executable prices using order-book depth.

    Returns:

        average_buy_price
        average_sell_price
        trade_quantity
        total_buy_cost
        total_sell_value

    Returns None when there is insufficient liquidity.
    """

    best_ask = getattr(buy_book, "best_ask", None)
    best_bid = getattr(sell_book, "best_bid", None)

    if best_ask is None or best_bid is None:
        return None

    best_ask_price = Decimal(str(best_ask.price))
    best_bid_price = Decimal(str(best_bid.price))

    if best_ask_price <= 0 or best_bid_price <= 0:
        return None

    # Determine how much base asset we want to buy.
    trade_quantity = trade_amount / best_ask_price

    if trade_quantity <= 0:
        return None

    # -------------------------------------------------
    # Minimum liquidity requirement
    # -------------------------------------------------

    required_trade_amount = (
        trade_amount * MIN_LIQUIDITY_MULTIPLIER
    )

    if required_trade_amount <= 0:
        return None

    try:
        total_buy_cost = buy_book.ask_cost(
            trade_quantity
        )

        total_sell_value = sell_book.bid_value(
            trade_quantity
        )

    except ValueError:
        # Not enough order-book liquidity.
        return None

    # Make sure both sides can support the required
    # trade value.
    if total_buy_cost < required_trade_amount:
        return None

    if total_sell_value < required_trade_amount:
        return None

    average_buy_price = (
        total_buy_cost / trade_quantity
    )

    average_sell_price = (
        total_sell_value / trade_quantity
    )

    return (
        average_buy_price,
        average_sell_price,
        trade_quantity,
        total_buy_cost,
        total_sell_value,
    )


def find_arbitrage_opportunities(
    order_books: Dict[Tuple[str, str], object],
    symbols: List[str],
    exchanges: List[str],
) -> List[ArbitrageOpportunity]:
    """
    Scan active order books and find executable arbitrage opportunities.

    The calculation uses:

        Order-book depth
        +
        Actual execution value
        +
        Buy fee
        +
        Sell fee
        +
        Order-book freshness
        +
        Minimum liquidity
        =
        Net profit
    """

    opportunities: List[ArbitrageOpportunity] = []

    for symbol in symbols:

        for buy_exchange in exchanges:

            for sell_exchange in exchanges:

                if buy_exchange == sell_exchange:
                    continue

                buy_book = order_books.get(
                    (buy_exchange, symbol)
                )

                sell_book = order_books.get(
                    (sell_exchange, symbol)
                )

                if buy_book is None or sell_book is None:
                    continue

                # -------------------------------------------------
                # Order-book freshness
                # -------------------------------------------------

                current_time = time.time()

                buy_age = (
                    current_time
                    - buy_book.timestamp
                )

                sell_age = (
                    current_time
                    - sell_book.timestamp
                )

                if (
                    buy_age > MAX_ORDER_BOOK_AGE_SECONDS
                    or sell_age > MAX_ORDER_BOOK_AGE_SECONDS
                ):
                    continue

                # -------------------------------------------------
                # Calculate executable trade
                # -------------------------------------------------

                execution = _calculate_execution(
                    buy_book=buy_book,
                    sell_book=sell_book,
                    trade_amount=TRADE_AMOUNT,
                )

                if execution is None:
                    continue

                (
                    average_buy_price,
                    average_sell_price,
                    trade_quantity,
                    total_buy_cost,
                    total_sell_value,
                ) = execution

                if average_sell_price <= average_buy_price:
                    continue

                # -------------------------------------------------
                # Fees
                # -------------------------------------------------

                buy_fee_rate = Decimal(
                    str(
                        settings.get_taker_fee(
                            buy_exchange
                        )
                    )
                )

                sell_fee_rate = Decimal(
                    str(
                        settings.get_taker_fee(
                            sell_exchange
                        )
                    )
                )

                # -------------------------------------------------
                # Actual fee calculation
                # -------------------------------------------------

                buy_fee = (
                    total_buy_cost
                    * buy_fee_rate
                )

                sell_fee = (
                    total_sell_value
                    * sell_fee_rate
                )

                # -------------------------------------------------
                # Actual money flow
                # -------------------------------------------------

                total_cost_with_fee = (
                    total_buy_cost
                    + buy_fee
                )

                total_revenue_after_fee = (
                    total_sell_value
                    - sell_fee
                )

                net_profit = (
                    total_revenue_after_fee
                    - total_cost_with_fee
                )

                # -------------------------------------------------
                # Gross spread
                # -------------------------------------------------

                gross_spread = (
                    average_sell_price
                    - average_buy_price
                )

                gross_spread_pct = (
                    gross_spread
                    / average_buy_price
                ) * Decimal("100")

                # -------------------------------------------------
                # Actual net ROI
                # -------------------------------------------------

                if total_cost_with_fee <= 0:
                    continue

                net_spread_pct = (
                    net_profit
                    / total_cost_with_fee
                ) * Decimal("100")

                # -------------------------------------------------
                # Combined fee percentage
                # -------------------------------------------------

                total_fee_pct = (
                    buy_fee_rate
                    + sell_fee_rate
                ) * Decimal("100")

                # -------------------------------------------------
                # Profitability
                # -------------------------------------------------

                is_profitable = (
                    net_spread_pct
                    >= MIN_PROFIT_PERCENTAGE
                )

                # -------------------------------------------------
                # Create opportunity
                # -------------------------------------------------

                opportunity = ArbitrageOpportunity(
                    symbol=symbol,
                    buy_exchange=buy_exchange,
                    sell_exchange=sell_exchange,
                    buy_price=float(
                        average_buy_price
                    ),
                    sell_price=float(
                        average_sell_price
                    ),
                    gross_spread=float(
                        gross_spread
                    ),
                    gross_spread_pct=float(
                        gross_spread_pct
                    ),
                    buy_fee=float(
                        buy_fee
                    ),
                    sell_fee=float(
                        sell_fee
                    ),
                    total_fee_pct=float(
                        total_fee_pct
                    ),
                    net_profit=float(
                        net_profit
                    ),
                    net_spread_pct=float(
                        net_spread_pct
                    ),
                    trade_quantity=float(
                        trade_quantity
                    ),
                    trade_amount=float(
                        TRADE_AMOUNT
                    ),
                    is_profitable=is_profitable,
                )

                opportunities.append(
                    opportunity
                )

                # -------------------------------------------------
                # Log profitable opportunities
                # -------------------------------------------------

                if is_profitable:
                    logger.info(
                        "[PROFITABLE OPP] %s | "
                        "Buy %s @ %.8f -> "
                        "Sell %s @ %.8f | "
                        "Amount: $%.2f | "
                        "Gross: %+0.4f%% | "
                        "Fees: -%.4f%% | "
                        "Profit: $%+.4f | "
                        "Net: %+0.4f%%",
                        symbol,
                        buy_exchange,
                        average_buy_price,
                        sell_exchange,
                        average_sell_price,
                        TRADE_AMOUNT,
                        gross_spread_pct,
                        total_fee_pct,
                        net_profit,
                        net_spread_pct,
                    )

    return opportunities