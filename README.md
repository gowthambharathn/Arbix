# ArbiX — Real-Time Cryptocurrency Arbitrage Pipeline

ArbiX is an asynchronous, high-performance cryptocurrency cross-exchange arbitrage system built with Python.

The project is designed to monitor cryptocurrency prices across multiple exchanges, normalize order book data, detect profitable arbitrage opportunities, and calculate potential net profit after accounting for trading fees, slippage, and execution costs.

> **Current Status:** Core domain models, high-precision order books, and clean asynchronous pipeline output are operational. Ready for Phase 1 live data integration.

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

---

### Asynchronous Pipeline & Standardized Logging

The application uses Python's `asyncio` framework for a non-blocking execution loop with clean logger output.

**Location:** `main.py`

Current capabilities include:

* Non-blocking `asyncio` event loop with graceful shutdown (`SIGINT` / `SIGTERM`).
* Clean, single-stream Python standard logging using `logger.info`.
* No stdout logging duplication.
* Real-time calculation of Gross Spread, Estimated Fees, and Net Profit.
* High-visibility profit detection tags:

  * `[PROFIT DETECTED]`
  * `[SCANNING]`

Example output:

```text
2026-09-07 20:58:37,212 | INFO | arbix | [SCANNING] Cycle 2 | Pair: BTC/USDT | Buy: $100048.96 | Sell: $100272.18 | Spread: $223.22 (0.22%)
2026-09-07 20:58:38,219 | INFO | arbix | [PROFIT DETECTED] Cycle 3 | Pair: BTC/USDT | Buy (Binance): $100044.97 | Sell (Coinbase): $100754.12 | Net Profit: $508.35 (0.51%)
```

---

## 🎯 ACTIVE PHASE: Phase 1 — Real Exchange Data Connectors

This is the current target phase to make ArbiX production-ready for live markets.

* [ ] **1. Async Exchange Clients:** Replace the synthetic `_market_data_simulator()` with live exchange connectors using `ccxt.pro` or native WebSockets.
* [ ] **2. WebSocket Data Streams:** Connect to real-time L2 order book WebSocket endpoints for Binance and Coinbase Advanced.
* [ ] **3. Order Book Synchronization:** Build an `OrderBookManager` to handle snapshot initialization and process incremental depth updates (deltas).
* [ ] **4. Normalization Layer:** Standardize raw exchange WebSocket messages into ArbiX `OrderBook` and `OrderBookLevel` objects.

---

## 📌 Full Development Roadmap

### Phase 1 — Real Exchange Data Connectors (IN PROGRESS)

* Real-time WebSocket streaming for Binance, Coinbase, and Kraken.
* L2 order book snapshot and delta synchronization.
* Exchange-specific message normalization.
* Automatic reconnection and connection health monitoring.
* Sequence-number validation to prevent stale or corrupted order books.

### Phase 2 — Dynamic Fee & Slippage Engine

* Replace hardcoded fee estimates with dynamic exchange taker/maker fee tiers.
* Depth-based slippage calculation using `ask_cost()` and `bid_proceeds()`.
* Account for network transfer fees and withdrawal costs.
* Calculate realistic net arbitrage profitability.

### Phase 3 — Trade Execution Engine

* Build an asynchronous `ExecutionEngine` for simultaneous buy/sell order placement using `asyncio.gather()`.
* Support pre-funded balance checks on both target exchanges.
* Add order state tracking:

  * `Pending`
  * `Filled`
  * `Partially Filled`
  * `Failed`
* Implement circuit breakers.
* Implement slippage caps.
* Add emergency kill switches.
* Handle exchange API failures and order execution errors.

### Phase 4 — Risk & Inventory Management

* Exchange balance tracking.
* Inventory allocation between exchanges.
* Automated rebalancing strategies.
* Auto-hedging.
* Exposure limits.
* Maximum trade-size controls.
* Risk-based opportunity filtering.

### Phase 5 — Monitoring & Infrastructure

* Prometheus metrics export:

  * WebSocket latency
  * Market-data latency
  * Opportunities detected
  * Trades executed
  * Profit detected vs. profit realized
  * Errors and reconnections
* Dockerization with `Dockerfile` and `docker-compose`.
* Centralized structured logging.
* Health checks.
* Alerting system via Telegram / Discord webhooks.
* Production deployment and process supervision.

---

## 🏗️ Project Architecture

```text
arbix/
│
├── config/
│   └── settings.py              # Settings & environment configuration
│
├── market_data/
│   └── order_book.py            # OrderBook and OrderBookLevel domain models
│
├── exchanges/
│   ├── base.py                  # Exchange client interface
│   ├── binance.py               # Binance WebSocket connector
│   ├── coinbase.py              # Coinbase WebSocket connector
│   └── kraken.py                # Kraken WebSocket connector
│
├── synchronization/
│   └── order_book_manager.py    # Snapshot & delta synchronization
│
├── normalization/
│   └── order_book_normalizer.py # Exchange → ArbiX normalization
│
├── main.py                      # Pipeline entry point & asyncio event loop
│
├── requirements.txt             # Dependencies
└── README.md                    # Project documentation
```

---

## 🚦 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/gowthambharathn/ArbiX.git
cd ArbiX
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

**Windows:**

```bash
venv\Scripts\activate
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Pipeline

```bash
python main.py
```

### 5. Run Automated Tests

```bash
python -m pytest -v
```

---

## 🔐 Trading Modes

| Mode    | Description                                                         |
| ------- | ------------------------------------------------------------------- |
| `paper` | Simulates market data and trade execution without financial risk.   |
| `live`  | Connects to real exchange APIs and executes trades with live funds. |

> ⚠️ **Warning:** Cryptocurrency arbitrage carries inherent market risk. Always validate software with paper trading before deploying capital.

---

## 🧪 Development Principles

ArbiX follows several principles to keep the system reliable and production-ready:

* **Asynchronous I/O** for low-latency market-data processing.
* **Decimal arithmetic** for financial precision.
* **Immutable domain models** to prevent accidental state corruption.
* **Exchange abstraction** to avoid exchange-specific logic leaking into the core domain.
* **Normalized market data** so the arbitrage engine works with a consistent data structure.
* **Automated testing** for domain logic and infrastructure.
* **Graceful shutdown** for safe service termination.
* **Paper trading first** before enabling live execution.

---

## 📈 Arbitrage Pipeline

```text
                    ┌─────────────────────┐
                    │   Exchange Streams  │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌───────────┐    ┌───────────┐    ┌───────────┐
        │  Binance  │    │ Coinbase  │    │  Kraken   │
        │ WebSocket │    │ WebSocket │    │ WebSocket │
        └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │ OrderBookManager    │
                    │ Snapshot + Deltas   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Normalization Layer │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ ArbiX OrderBook     │
                    │ Domain Model        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Arbitrage Detector  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Fee & Slippage      │
                    │ Engine               │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Execution Engine    │
                    └─────────────────────┘
```

---

## 🎯 Production Goal

The ultimate goal of ArbiX is to build a reliable, low-latency, production-grade cryptocurrency arbitrage platform capable of:

1. Receiving real-time market data from multiple exchanges.
2. Maintaining synchronized L2 order books.
3. Detecting cross-exchange arbitrage opportunities.
4. Calculating realistic profitability after fees and slippage.
5. Executing simultaneous buy/sell orders.
6. Managing balances, inventory, and risk.
7. Monitoring system health and trading performance.

The system will initially operate in **paper trading mode** before any live capital is exposed.

---

## 👨‍💻 Author

**Gowtham Bharath**

Android Developer • Python Developer • AI/ML Enthusiast

---

⭐ If you find ArbiX interesting, consider starring the repository.
