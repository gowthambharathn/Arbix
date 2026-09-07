import os

# Strategy Parameters
SYMBOL = "BTC/USDT"
TAKER_FEE = 0.001  # 0.1% standard exchange taker fee
MIN_PROFIT_USDT = 1.0  # Minimum target profit in USDT before executing

# API Credentials (from environment variables)
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")