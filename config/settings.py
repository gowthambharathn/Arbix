"""
ArbiX Configuration Settings

Centralized configuration management for the ArbiX
cryptocurrency arbitrage trading system.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum

from dotenv import load_dotenv


load_dotenv()


class TradingMode(str, Enum):
    """Supported trading modes."""

    PAPER = "paper"
    LIVE = "live"


@dataclass(frozen=True)
class Settings:
    """Application-wide configuration for ArbiX."""

    exchange_api_key: str
    exchange_api_secret: str

    trading_mode: TradingMode

    min_profit_percentage: float
    max_trade_amount: float

    def validate(self) -> None:
        """Validate application configuration."""

        if self.min_profit_percentage < 0:
            raise ValueError(
                "MIN_PROFIT_PERCENTAGE cannot be negative."
            )

        if self.max_trade_amount <= 0:
            raise ValueError(
                "MAX_TRADE_AMOUNT must be greater than zero."
            )

        if self.trading_mode == TradingMode.LIVE:
            if not self.exchange_api_key:
                raise ValueError(
                    "EXCHANGE_API_KEY is required in live mode."
                )

            if not self.exchange_api_secret:
                raise ValueError(
                    "EXCHANGE_API_SECRET is required in live mode."
                )


def _get_trading_mode() -> TradingMode:
    """Read and validate the configured trading mode."""

    value = os.getenv("TRADING_MODE", TradingMode.PAPER.value).lower()

    try:
        return TradingMode(value)
    except ValueError as error:
        raise ValueError(
            f"Invalid TRADING_MODE: '{value}'. "
            f"Expected one of: "
            f"{', '.join(mode.value for mode in TradingMode)}."
        ) from error


def load_settings() -> Settings:
    """Load application settings from environment variables."""

    settings = Settings(
        exchange_api_key=os.getenv("EXCHANGE_API_KEY", ""),
        exchange_api_secret=os.getenv("EXCHANGE_API_SECRET", ""),
        trading_mode=_get_trading_mode(),
        min_profit_percentage=float(
            os.getenv("MIN_PROFIT_PERCENTAGE", "0.20")
        ),
        max_trade_amount=float(
            os.getenv("MAX_TRADE_AMOUNT", "100")
        ),
    )

    settings.validate()

    return settings


settings = load_settings()