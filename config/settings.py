"""
ArbiX Configuration Settings
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from dotenv import load_dotenv


load_dotenv()


class TradingMode(str, Enum):
    """Supported trading modes."""

    PAPER = "paper"
    LIVE = "live"


@dataclass(frozen=True)
class Settings:
    """Application-wide configuration for ArbiX."""

    symbols: List[str]
    exchanges: List[str]
    trading_mode: TradingMode

    exchange_api_key: str
    exchange_api_secret: str

    min_profit_percentage: float
    max_trade_amount: float
    paper_balance_usdt: float

    exchange_taker_fees: Dict[str, float]

    @property
    def symbol(self) -> str:
        """Return the first configured symbol for backward compatibility."""
        return self.symbols[0] if self.symbols else "BTC/USDT"

    def get_taker_fee(self, exchange: str) -> float:
        """Return the configured taker fee for an exchange."""
        return self.exchange_taker_fees.get(exchange.lower(), 0.001)


def _get_symbols() -> List[str]:
    """Return normalized trading symbols from the environment."""

    symbols = os.getenv(
        "TRADING_SYMBOLS",
        "SOL/USDT,XRP/USDT,BNB/USDT,DOGE/USDT,SUI/USDT",
    )

    return [
        symbol.strip().upper()
        for symbol in symbols.split(",")
        if symbol.strip()
    ]


def _get_exchanges() -> List[str]:
    """Return normalized exchange names from the environment."""

    exchanges = os.getenv(
        "EXCHANGES",
        "binance,bybit,okx",
    )

    return [
        exchange.strip().lower()
        for exchange in exchanges.split(",")
        if exchange.strip()
    ]


def load_settings() -> Settings:
    """Load application settings from environment variables."""

    exchange_taker_fees = {
        "binance": float(
            os.getenv("BINANCE_TAKER_FEE", "0.001")
        ),
        "bybit": float(
            os.getenv("BYBIT_TAKER_FEE", "0.001")
        ),
        "okx": float(
            os.getenv("OKX_TAKER_FEE", "0.001")
        ),
    }

    return Settings(
        symbols=_get_symbols(),
        exchanges=_get_exchanges(),
        trading_mode=TradingMode.PAPER,
        exchange_api_key=os.getenv("EXCHANGE_API_KEY", ""),
        exchange_api_secret=os.getenv("EXCHANGE_API_SECRET", ""),
        min_profit_percentage=float(
            os.getenv("MIN_PROFIT_PERCENTAGE", "0.20")
        ),
        max_trade_amount=float(
            os.getenv("MAX_TRADE_AMOUNT", "100.0")
        ),
        paper_balance_usdt=float(
            os.getenv("PAPER_BALANCE_USDT", "1000.0")
        ),
        exchange_taker_fees=exchange_taker_fees,
    )


settings = load_settings()