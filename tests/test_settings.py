import pytest

from config.settings import (
    Settings,
    TradingMode,
    _get_trading_mode,
    load_settings,
)


def test_trading_mode_values():
    """TradingMode should contain paper and live modes."""

    assert TradingMode.PAPER.value == "paper"
    assert TradingMode.LIVE.value == "live"


def test_load_settings_with_defaults(monkeypatch):
    """Settings should load default values when environment variables are missing."""

    monkeypatch.delenv("EXCHANGE_API_KEY", raising=False)
    monkeypatch.delenv("EXCHANGE_API_SECRET", raising=False)
    monkeypatch.delenv("TRADING_MODE", raising=False)
    monkeypatch.delenv("MIN_PROFIT_PERCENTAGE", raising=False)
    monkeypatch.delenv("MAX_TRADE_AMOUNT", raising=False)

    settings = load_settings()

    assert settings.exchange_api_key == ""
    assert settings.exchange_api_secret == ""
    assert settings.trading_mode == TradingMode.PAPER
    assert settings.min_profit_percentage == 0.20
    assert settings.max_trade_amount == 100.0


def test_load_settings_with_custom_values(monkeypatch):
    """Settings should load custom values from environment variables."""

    monkeypatch.setenv("EXCHANGE_API_KEY", "test_key")
    monkeypatch.setenv("EXCHANGE_API_SECRET", "test_secret")
    monkeypatch.setenv("TRADING_MODE", "paper")
    monkeypatch.setenv("MIN_PROFIT_PERCENTAGE", "0.50")
    monkeypatch.setenv("MAX_TRADE_AMOUNT", "500")

    settings = load_settings()

    assert settings.exchange_api_key == "test_key"
    assert settings.exchange_api_secret == "test_secret"
    assert settings.trading_mode == TradingMode.PAPER
    assert settings.min_profit_percentage == 0.50
    assert settings.max_trade_amount == 500.0


def test_trading_mode_is_case_insensitive(monkeypatch):
    """Trading mode should be converted to lowercase before validation."""

    monkeypatch.setenv("TRADING_MODE", "LIVE")

    mode = _get_trading_mode()

    assert mode == TradingMode.LIVE


def test_invalid_trading_mode_raises_error(monkeypatch):
    """Invalid trading modes should raise ValueError."""

    monkeypatch.setenv("TRADING_MODE", "invalid_mode")

    with pytest.raises(
        ValueError,
        match="Invalid TRADING_MODE"
    ):
        _get_trading_mode()


def test_negative_min_profit_percentage_raises_error():
    """Negative minimum profit percentage should not be allowed."""

    settings = Settings(
        exchange_api_key="",
        exchange_api_secret="",
        trading_mode=TradingMode.PAPER,
        min_profit_percentage=-0.01,
        max_trade_amount=100.0,
    )

    with pytest.raises(
        ValueError,
        match="MIN_PROFIT_PERCENTAGE cannot be negative"
    ):
        settings.validate()


@pytest.mark.parametrize(
    "max_trade_amount",
    [0, -1, -100.0],
)
def test_invalid_max_trade_amount_raises_error(max_trade_amount):
    """Zero or negative trade amounts should not be allowed."""

    settings = Settings(
        exchange_api_key="",
        exchange_api_secret="",
        trading_mode=TradingMode.PAPER,
        min_profit_percentage=0.20,
        max_trade_amount=max_trade_amount,
    )

    with pytest.raises(
        ValueError,
        match="MAX_TRADE_AMOUNT must be greater than zero"
    ):
        settings.validate()


def test_live_mode_requires_api_key():
    """Live mode should require an API key."""

    settings = Settings(
        exchange_api_key="",
        exchange_api_secret="test_secret",
        trading_mode=TradingMode.LIVE,
        min_profit_percentage=0.20,
        max_trade_amount=100.0,
    )

    with pytest.raises(
        ValueError,
        match="EXCHANGE_API_KEY is required in live mode"
    ):
        settings.validate()


def test_live_mode_requires_api_secret():
    """Live mode should require an API secret."""

    settings = Settings(
        exchange_api_key="test_key",
        exchange_api_secret="",
        trading_mode=TradingMode.LIVE,
        min_profit_percentage=0.20,
        max_trade_amount=100.0,
    )

    with pytest.raises(
        ValueError,
        match="EXCHANGE_API_SECRET is required in live mode"
    ):
        settings.validate()


def test_valid_live_mode_settings():
    """Valid live mode settings should pass validation."""

    settings = Settings(
        exchange_api_key="test_key",
        exchange_api_secret="test_secret",
        trading_mode=TradingMode.LIVE,
        min_profit_percentage=0.20,
        max_trade_amount=100.0,
    )

    settings.validate()


def test_paper_mode_does_not_require_api_credentials():
    """Paper mode should work without API credentials."""

    settings = Settings(
        exchange_api_key="",
        exchange_api_secret="",
        trading_mode=TradingMode.PAPER,
        min_profit_percentage=0.20,
        max_trade_amount=100.0,
    )

    settings.validate()


def test_load_settings_rejects_negative_profit_percentage(monkeypatch):
    """Loading settings should reject a negative profit percentage."""

    monkeypatch.setenv("MIN_PROFIT_PERCENTAGE", "-1")
    monkeypatch.setenv("MAX_TRADE_AMOUNT", "100")
    monkeypatch.setenv("TRADING_MODE", "paper")

    with pytest.raises(
        ValueError,
        match="MIN_PROFIT_PERCENTAGE cannot be negative"
    ):
        load_settings()


def test_load_settings_rejects_zero_trade_amount(monkeypatch):
    """Loading settings should reject zero maximum trade amount."""

    monkeypatch.setenv("MIN_PROFIT_PERCENTAGE", "0.20")
    monkeypatch.setenv("MAX_TRADE_AMOUNT", "0")
    monkeypatch.setenv("TRADING_MODE", "paper")

    with pytest.raises(
        ValueError,
        match="MAX_TRADE_AMOUNT must be greater than zero"
    ):
        load_settings()


def test_load_settings_live_mode_requires_credentials(monkeypatch):
    """Loading live mode settings without credentials should fail."""

    monkeypatch.delenv("EXCHANGE_API_KEY", raising=False)
    monkeypatch.delenv("EXCHANGE_API_SECRET", raising=False)
    monkeypatch.setenv("TRADING_MODE", "live")
    monkeypatch.setenv("MIN_PROFIT_PERCENTAGE", "0.20")
    monkeypatch.setenv("MAX_TRADE_AMOUNT", "100")

    with pytest.raises(
        ValueError,
        match="EXCHANGE_API_KEY is required in live mode"
    ):
        load_settings()


def test_load_settings_valid_live_mode(monkeypatch):
    """Loading valid live mode configuration should succeed."""

    monkeypatch.setenv("EXCHANGE_API_KEY", "test_key")
    monkeypatch.setenv("EXCHANGE_API_SECRET", "test_secret")
    monkeypatch.setenv("TRADING_MODE", "live")
    monkeypatch.setenv("MIN_PROFIT_PERCENTAGE", "0.30")
    monkeypatch.setenv("MAX_TRADE_AMOUNT", "250")

    settings = load_settings()

    assert settings.exchange_api_key == "test_key"
    assert settings.exchange_api_secret == "test_secret"
    assert settings.trading_mode == TradingMode.LIVE
    assert settings.min_profit_percentage == 0.30
    assert settings.max_trade_amount == 250.0