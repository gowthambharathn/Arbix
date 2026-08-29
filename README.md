# ArbiX — Real-Time Cryptocurrency Arbitrage Pipeline

ArbiX is an asynchronous, high-performance cryptocurrency cross-exchange arbitrage system built with Python.

The project is designed to monitor cryptocurrency prices across multiple exchanges, normalize order book data, detect profitable arbitrage opportunities, and calculate potential net profit after accounting for trading fees, slippage, and execution costs.

> **Current Status:** Core domain models and the asynchronous market simulation pipeline are implemented and operational.

---

## 🚀 Current Features

### Immutable Order Book Domain Model

The project includes a high-precision order book implementation designed for financial calculations.

**Location:** `market_data/order_book.py`

Features include:

* High-precision price and volume calculations using Python's `Decimal`.
* Immutable `OrderBookLevel` and `OrderBook` domain models.
* Factory-based order book creation using `create_order_book()`.
* Best market price helpers:

  * `best_bid`
  * `best_ask`
* Spread calculations:

  * `spread`
  * `spread_percentage`
* Liquidity and execution helpers:

  * `ask_cost()`
  * `bid_value()`
  * `bid_proceeds()`
* Tuple-based helpers for compatibility:

  * `get_best_bid()`
  * `get_best_ask()`

---

## ⚡ Asynchronous Market Data Pipeline

The application uses Python's `asyncio` framework to support a non-blocking, asynchronous execution pipeline.

**Location:** `main.py`

Current capabilities include:

* Fully asynchronous event loop using `asyncio`.
* Background market data simulation.
* Continuous market tick processing.
* Dynamic arbitrage spread monitoring.
* Calculation of:

  * Gross Spread
  * Estimated Trading Fees
  * Net Profit Percentage
* Detection and logging of potentially profitable opportunities.
* Clear distinction between normal market scanning and actionable opportunities.
* Graceful shutdown handling using:

  * `SIGINT`
  * `SIGTERM`

Example output:

```text
[SCAN] BTC/USDT | Binance: 100000 | Kraken: 100150
[PROFIT DETECTED] Net Profit: 0.35%
```

---

# 🏗️ Project Architecture

```text
arbix/
│
├── config/
│   └── settings.py
│       # Configuration management and environment variables
│
├── market_data/
│   └── order_book.py
│       # OrderBook and OrderBookLevel domain models
│
├── main.py
│   # Application entry point and asynchronous simulation runner
│
├── requirements.txt
│   # Python dependencies
│
└── README.md
    # Project documentation
```

---

# 🚦 Quick Start

## Prerequisites

Before running ArbiX, make sure you have:

* Python 3.10 or higher
* Git

## 1. Clone the Repository

```bash
git clone https://github.com/gowthambharathn/ArbiX.git
cd ArbiX
```

## 2. Create a Virtual Environment

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure Environment Variables

Create a `.env` file in the project root if required by your configuration.

Example:

```env
TRADING_MODE=paper
MIN_PROFIT_PERCENTAGE=0.2
MAX_TRADE_AMOUNT=100
```

> **Important:** Never commit API keys or other sensitive credentials to GitHub.

## 5. Run the Application

```bash
python main.py
```

---

# 🧪 Testing

ArbiX uses `pytest` for automated testing.

Run the complete test suite:

```bash
python -m pytest -v
```

Run a specific test file:

```bash
python -m pytest tests/test_settings.py -v
```

Example output:

```text
============================= test session starts =============================
collected 17 items

tests/test_settings.py ................. PASSED

============================== 17 passed ==============================
```

---

# 📌 Development Roadmap

The following roadmap outlines the planned development of ArbiX from a market simulation system into a more complete arbitrage trading platform.

## Phase 1 — Real Exchange Data Connectors

* [ ] Replace the simulated market data pipeline with real exchange connections.
* [ ] Integrate real-time WebSocket streams.
* [ ] Add support for:

  * Binance
  * Coinbase Advanced
  * Kraken
* [ ] Evaluate `ccxt.pro` and native WebSocket implementations.
* [ ] Implement an `OrderBookManager`.
* [ ] Process incremental depth and delta updates.
* [ ] Maintain synchronized L2 order books.

---

## Phase 2 — Dynamic Fee & Slippage Engine

* [ ] Replace hardcoded trading fee estimates with exchange-specific fee configurations.
* [ ] Support different trading fee tiers.
* [ ] Implement depth-based slippage calculations.
* [ ] Calculate execution cost using actual order book liquidity.
* [ ] Use:

  * `ask_cost()`
  * `bid_value()`
  * `bid_proceeds()`
* [ ] Account for withdrawal and network fees.
* [ ] Calculate realistic net profitability before trade execution.

---

## Phase 3 — Trade Execution Engine

* [ ] Build an asynchronous `ExecutionEngine`.
* [ ] Place orders across multiple exchanges.
* [ ] Support market and limit orders.
* [ ] Implement simultaneous or coordinated order execution.
* [ ] Track order states:

  * Pending
  * Open
  * Partially Filled
  * Filled
  * Cancelled
  * Failed
* [ ] Implement execution timeout handling.
* [ ] Add retry strategies where appropriate.

### Safety Mechanisms

* [ ] Circuit breakers.
* [ ] Maximum slippage limits.
* [ ] Maximum trade size limits.
* [ ] Daily loss limits.
* [ ] Emergency kill switch.
* [ ] Exchange connectivity monitoring.

---

## Phase 4 — Risk & Inventory Management

* [ ] Implement an exchange balance manager.
* [ ] Verify available balances before executing trades.
* [ ] Track asset inventory across exchanges.
* [ ] Prevent trades when insufficient liquidity or balance is available.
* [ ] Implement exchange inventory rebalancing.
* [ ] Explore asset transfer strategies.
* [ ] Explore hedging mechanisms using:

  * Triangular arbitrage
  * Perpetual futures
  * Cross-exchange hedging

---

## Phase 5 — Monitoring, Metrics & Infrastructure

* [ ] Add Prometheus metrics.
* [ ] Track:

  * Market data latency
  * Order book update latency
  * Detected spread percentage
  * Net expected profit
  * Executed trades
  * Trade PnL
  * System errors
* [ ] Create monitoring dashboards.
* [ ] Dockerize the application.
* [ ] Add `docker-compose` for local deployment.
* [ ] Implement structured logging.
* [ ] Add persistent trade history.
* [ ] Set up alerts through:

  * Telegram
  * Discord
  * Webhooks

---

# 🔐 Trading Modes

ArbiX is designed to support multiple trading modes.

| Mode    | Description                                                     |
| ------- | --------------------------------------------------------------- |
| `paper` | Simulates trades without using real funds.                      |
| `live`  | Executes real trades using configured exchange API credentials. |

> ⚠️ **Warning:** Live trading involves financial risk. Thorough testing, risk management, and validation should be completed before connecting the system to real funds.

---

# 🛠️ Technology Stack

* **Python**
* **Asyncio**
* **Decimal**
* **Pytest**
* **Python Dotenv**
* **WebSockets** *(planned)*
* **CCXT / CCXT Pro** *(planned)*
* **Prometheus** *(planned)*
* **Docker** *(planned)*

---

# 🎯 Project Goals

The goal of ArbiX is to build a modular and scalable arbitrage trading architecture capable of:

1. Receiving real-time market data from multiple exchanges.
2. Normalizing exchange-specific order book formats.
3. Detecting profitable cross-exchange price differences.
4. Calculating realistic profitability after fees and slippage.
5. Managing exchange balances and risk.
6. Executing trades with low latency.
7. Monitoring performance and system health.
8. Supporting safe paper trading before live deployment.

---

# ⚠️ Disclaimer

ArbiX is an experimental software project intended for educational and research purposes.

Cryptocurrency trading involves significant financial risk. The software does not guarantee profitability, and the authors are not responsible for financial losses resulting from the use of this project.

Always test strategies using paper trading before considering live execution.

---

# 📄 License

This project is licensed under the MIT License.

See the `LICENSE` file for more information.

---

# 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

To contribute:

```bash
# Fork the repository

# Create a feature branch
git checkout -b feature/your-feature-name

# Commit your changes
git commit -m "Add your feature"

# Push your branch
git push origin feature/your-feature-name
```

Then open a Pull Request.

---

## 👨‍💻 Author

**Gowtham Bharath**

Android Developer • Python Developer • AI/ML Enthusiast

Building scalable software, intelligent systems, and exploring algorithmic trading and machine learning.
