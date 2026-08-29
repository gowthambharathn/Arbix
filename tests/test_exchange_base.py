import inspect
from decimal import Decimal

import pytest

from exchanges.base import (
    ExchangeAuthenticationError,
    ExchangeBalance,
    ExchangeClient,
    ExchangeConnectionError,
    ExchangeError,
    ExchangeOrderError,
    ExchangeOrderSide,
    ExchangeOrderType,
    ExchangeRateLimitError,
    OrderSubmission,
    Ticker,
    TradingFee,
)


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


def test_exchange_exceptions_inherit_from_exchange_error():
    """All exchange-specific exceptions should inherit from ExchangeError."""

    assert issubclass(ExchangeConnectionError, ExchangeError)
    assert issubclass(ExchangeAuthenticationError, ExchangeError)
    assert issubclass(ExchangeRateLimitError, ExchangeError)
    assert issubclass(ExchangeOrderError, ExchangeError)


def test_exchange_error_is_exception():
    """ExchangeError should ultimately inherit from Exception."""

    assert issubclass(ExchangeError, Exception)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


def test_exchange_order_side_values():
    """ExchangeOrderSide should contain BUY and SELL."""

    assert ExchangeOrderSide.BUY.value == "buy"
    assert ExchangeOrderSide.SELL.value == "sell"


def test_exchange_order_type_values():
    """ExchangeOrderType should contain MARKET and LIMIT."""

    assert ExchangeOrderType.MARKET.value == "market"
    assert ExchangeOrderType.LIMIT.value == "limit"


# ---------------------------------------------------------------------------
# Ticker
# ---------------------------------------------------------------------------


def test_ticker_creation():
    """Ticker should store valid market data correctly."""

    ticker = Ticker(
        exchange="binance",
        symbol="BTC/USDT",
        bid=Decimal("100"),
        ask=Decimal("101"),
        timestamp=1000.0,
    )

    assert ticker.exchange == "binance"
    assert ticker.symbol == "BTC/USDT"
    assert ticker.bid == Decimal("100")
    assert ticker.ask == Decimal("101")
    assert ticker.timestamp == 1000.0


def test_ticker_spread():
    """Ticker spread should equal ask minus bid."""

    ticker = Ticker(
        exchange="binance",
        symbol="BTC/USDT",
        bid=Decimal("100"),
        ask=Decimal("101.50"),
        timestamp=1000.0,
    )

    assert ticker.spread == Decimal("1.50")


def test_ticker_mid_price():
    """Ticker midpoint should equal the average of bid and ask."""

    ticker = Ticker(
        exchange="binance",
        symbol="BTC/USDT",
        bid=Decimal("100"),
        ask=Decimal("102"),
        timestamp=1000.0,
    )

    assert ticker.mid_price == Decimal("101")


def test_ticker_rejects_empty_exchange():
    """Ticker should reject an empty exchange name."""

    with pytest.raises(
        ValueError,
        match="Exchange cannot be empty",
    ):
        Ticker(
            exchange="",
            symbol="BTC/USDT",
            bid=Decimal("100"),
            ask=Decimal("101"),
            timestamp=1000.0,
        )


def test_ticker_rejects_empty_symbol():
    """Ticker should reject an empty trading symbol."""

    with pytest.raises(
        ValueError,
        match="Symbol cannot be empty",
    ):
        Ticker(
            exchange="binance",
            symbol="",
            bid=Decimal("100"),
            ask=Decimal("101"),
            timestamp=1000.0,
        )


@pytest.mark.parametrize(
    "bid",
    [
        Decimal("0"),
        Decimal("-1"),
    ],
)
def test_ticker_rejects_invalid_bid(bid):
    """Ticker should reject zero or negative bid prices."""

    with pytest.raises(
        ValueError,
        match="Bid price must be greater than zero",
    ):
        Ticker(
            exchange="binance",
            symbol="BTC/USDT",
            bid=bid,
            ask=Decimal("101"),
            timestamp=1000.0,
        )


@pytest.mark.parametrize(
    "ask",
    [
        Decimal("0"),
        Decimal("-1"),
    ],
)
def test_ticker_rejects_invalid_ask(ask):
    """Ticker should reject zero or negative ask prices."""

    with pytest.raises(
        ValueError,
        match="Ask price must be greater than zero",
    ):
        Ticker(
            exchange="binance",
            symbol="BTC/USDT",
            bid=Decimal("100"),
            ask=ask,
            timestamp=1000.0,
        )


def test_ticker_rejects_ask_below_bid():
    """Ticker should reject an ask price below the bid price."""

    with pytest.raises(
        ValueError,
        match="Ask price cannot be lower than bid price",
    ):
        Ticker(
            exchange="binance",
            symbol="BTC/USDT",
            bid=Decimal("101"),
            ask=Decimal("100"),
            timestamp=1000.0,
        )


def test_ticker_rejects_invalid_timestamp():
    """Ticker should reject zero or negative timestamps."""

    with pytest.raises(
        ValueError,
        match="Ticker timestamp must be greater than zero",
    ):
        Ticker(
            exchange="binance",
            symbol="BTC/USDT",
            bid=Decimal("100"),
            ask=Decimal("101"),
            timestamp=0,
        )


def test_ticker_is_immutable():
    """Ticker should be immutable because it is a frozen dataclass."""

    ticker = Ticker(
        exchange="binance",
        symbol="BTC/USDT",
        bid=Decimal("100"),
        ask=Decimal("101"),
        timestamp=1000.0,
    )

    with pytest.raises(AttributeError):
        ticker.bid = Decimal("200")


# ---------------------------------------------------------------------------
# TradingFee
# ---------------------------------------------------------------------------


def test_trading_fee_creation():
    """TradingFee should store maker and taker fees."""

    fee = TradingFee(
        maker=Decimal("0.10"),
        taker=Decimal("0.20"),
    )

    assert fee.maker == Decimal("0.10")
    assert fee.taker == Decimal("0.20")


def test_trading_fee_allows_zero_fees():
    """Zero trading fees should be valid."""

    fee = TradingFee(
        maker=Decimal("0"),
        taker=Decimal("0"),
    )

    assert fee.maker == Decimal("0")
    assert fee.taker == Decimal("0")


def test_trading_fee_rejects_negative_maker_fee():
    """Maker fee should not be negative."""

    with pytest.raises(
        ValueError,
        match="Maker fee cannot be negative",
    ):
        TradingFee(
            maker=Decimal("-0.01"),
            taker=Decimal("0.20"),
        )


def test_trading_fee_rejects_negative_taker_fee():
    """Taker fee should not be negative."""

    with pytest.raises(
        ValueError,
        match="Taker fee cannot be negative",
    ):
        TradingFee(
            maker=Decimal("0.10"),
            taker=Decimal("-0.01"),
        )


def test_trading_fee_is_immutable():
    """TradingFee should be immutable because it is a frozen dataclass."""

    fee = TradingFee(
        maker=Decimal("0.10"),
        taker=Decimal("0.20"),
    )

    with pytest.raises(AttributeError):
        fee.maker = Decimal("0.30")


# ---------------------------------------------------------------------------
# OrderSubmission
# ---------------------------------------------------------------------------


def test_order_submission_creation():
    """OrderSubmission should store order execution information."""

    submission = OrderSubmission(
        exchange_order_id="order-123",
        status="filled",
        filled_quantity=Decimal("0.5"),
        average_fill_price=Decimal("50000"),
    )

    assert submission.exchange_order_id == "order-123"
    assert submission.status == "filled"
    assert submission.filled_quantity == Decimal("0.5")
    assert submission.average_fill_price == Decimal("50000")
    assert submission.message == ""


def test_order_submission_accepts_message():
    """OrderSubmission should store an optional message."""

    submission = OrderSubmission(
        exchange_order_id="order-123",
        status="rejected",
        filled_quantity=Decimal("0"),
        average_fill_price=Decimal("0"),
        message="Insufficient balance",
    )

    assert submission.message == "Insufficient balance"


def test_order_submission_is_immutable():
    """OrderSubmission should be immutable because it is a frozen dataclass."""

    submission = OrderSubmission(
        exchange_order_id="order-123",
        status="filled",
        filled_quantity=Decimal("0.5"),
        average_fill_price=Decimal("50000"),
    )

    with pytest.raises(AttributeError):
        submission.status = "cancelled"


# ---------------------------------------------------------------------------
# ExchangeBalance
# ---------------------------------------------------------------------------


def test_exchange_balance_creation():
    """ExchangeBalance should store available and locked balances."""

    balance = ExchangeBalance(
        asset="USDT",
        available=Decimal("1000"),
        locked=Decimal("250"),
    )

    assert balance.asset == "USDT"
    assert balance.available == Decimal("1000")
    assert balance.locked == Decimal("250")


def test_exchange_balance_total():
    """Total balance should equal available plus locked balance."""

    balance = ExchangeBalance(
        asset="USDT",
        available=Decimal("1000"),
        locked=Decimal("250"),
    )

    assert balance.total == Decimal("1250")


def test_exchange_balance_is_immutable():
    """ExchangeBalance should be immutable because it is a frozen dataclass."""

    balance = ExchangeBalance(
        asset="USDT",
        available=Decimal("1000"),
        locked=Decimal("250"),
    )

    with pytest.raises(AttributeError):
        balance.available = Decimal("500")


# ---------------------------------------------------------------------------
# ExchangeClient abstraction
# ---------------------------------------------------------------------------


def test_exchange_client_is_abstract():
    """ExchangeClient should not be directly instantiable."""

    with pytest.raises(TypeError):
        ExchangeClient()


def test_exchange_client_declares_required_methods():
    """ExchangeClient should expose all required abstract operations."""

    expected_methods = {
        "connect",
        "close",
        "get_ticker",
        "get_order_book",
        "get_balance",
        "get_trading_fee",
        "submit_order",
        "cancel_order",
        "get_order",
    }

    for method_name in expected_methods:
        assert hasattr(ExchangeClient, method_name)


def test_exchange_client_methods_are_abstract():
    """Required ExchangeClient operations should be abstract."""

    expected_methods = {
        "connect",
        "close",
        "get_ticker",
        "get_order_book",
        "get_balance",
        "get_trading_fee",
        "submit_order",
        "cancel_order",
        "get_order",
    }

    for method_name in expected_methods:
        method = getattr(ExchangeClient, method_name)
        assert getattr(method, "__isabstractmethod__", False)


def test_exchange_client_name_property_is_abstract():
    """ExchangeClient.name should be an abstract property."""

    name_property = inspect.getattr_static(
        ExchangeClient,
        "name",
    )

    assert isinstance(name_property, property)
    assert name_property.__isabstractmethod__


def test_exchange_client_uses_async_methods():
    """ExchangeClient exchange operations should be asynchronous."""

    async_methods = {
        "connect",
        "close",
        "get_ticker",
        "get_order_book",
        "get_balance",
        "get_trading_fee",
        "submit_order",
        "cancel_order",
        "get_order",
    }

    for method_name in async_methods:
        method = getattr(ExchangeClient, method_name)
        assert inspect.iscoroutinefunction(method)