# ArbiX — Cross-Exchange Crypto Arbitrage Bot

**ArbiX** is an asynchronous, high-performance cryptocurrency arbitrage system built with **Python** and **CCXT Pro**.

The system continuously streams real-time order book data from multiple cryptocurrency exchanges, detects cross-exchange price discrepancies, evaluates profitability using market depth and trading fees, and simulates arbitrage execution through a paper trading engine.

> **Current focus:** Building a reliable real-time market data and arbitrage detection infrastructure before moving toward live trading.

---

## 🚀 Features

### Real-Time Market Data

* Asynchronous WebSocket market data streaming using **CCXT Pro**
* Real-time order book updates from multiple exchanges
* Currently supports:

  * Binance
  * Bybit
  * Kraken
* Automatic stream reconnection
* Exception handling for disconnected or failed feeds
* Multi-exchange order book caching

### Order Book Processing

* Structured order book data models
* `OrderBookLevel` model for individual bid/ask levels
* Price and quantity tracking
* Conversion of raw exchange responses into normalized internal models
* Market-depth-aware opportunity evaluation

### Arbitrage Detection

* Cross-exchange bid/ask comparison
* Automatic scanning across active exchanges
* Gross spread calculation
* Net profitability calculation
* Trading-fee consideration
* Market-depth and slippage analysis
* Timestamped arbitrage opportunities

### Paper Trading

* Simulated arbitrage execution
* Virtual USDT balance
* Trade history tracking
* Fee-aware profit calculation
* No real funds are used during paper trading

### Monitoring & Reliability

* Periodic system heartbeat logs
* Active exchange/order-book monitoring
* WebSocket reconnect handling
* Graceful shutdown on interruption or task cancellation

---

## 🏗️ Architecture

ArbiX is designed as a modular asynchronous pipeline:

```text
                     ┌──────────────────────┐
                     │    Cryptocurrency    │
                     │      Exchanges       │
                     └──────────┬───────────┘
                                │
                    WebSocket Order Books
                                │
                                ▼
                 ┌──────────────────────────┐
                 │      Market Data Layer   │
                 │                          │
                 │  • Streamer              │
                 │  • Exchange Connections  │
                 │  • Order Book Cache      │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │    Order Book Models     │
                 │                          │
                 │  • Price                 │
                 │  • Amount                │
                 │  • Bids / Asks            │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │    Arbitrage Finder      │
                 │                          │
                 │  • Cross-exchange scan   │
                 │  • Spread detection      │
                 │  • Opportunity creation  │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │  Profitability Engine    │
                 │                          │
                 │  • Trading fees          │
                 │  • Slippage              │
                 │  • Market depth          │
                 │  • Net profit            │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │     Paper Trading        │
                 │                          │
                 │  • Virtual balance       │
                 │  • Trade execution       │
                 │  • Trade history         │
                 └──────────────────────────┘
```

---

## 📁 Project Structure

```text
ArbiX/
│
├── arbitrage/
│   ├── calculator.py
│   ├── finder.py
│   └── opportunity.py
│
├── engine/
│   └── paper_engine.py
│
├── market_data/
│   ├── order_book.py
│   └── streamer.py
│
├── config/
│   └── settings.py
│
├── tests/
│   └── ...
│
├── main.py
├── requirements.txt
├── README.md
└── ...
```

> The exact project structure may evolve as additional arbitrage strategies and execution modules are introduced.

---

## 📊 Current Pipeline

The current system follows this flow:

```text
Exchange WebSockets
        │
        ▼
Real-Time Order Books
        │
        ▼
Normalize Market Data
        │
        ▼
Cache Exchange Order Books
        │
        ▼
Scan Cross-Exchange Prices
        │
        ▼
Calculate Gross Spread
        │
        ▼
Apply Fees + Slippage
        │
        ▼
Calculate Net Profitability
        │
        ▼
Create Arbitrage Opportunity
        │
        ▼
Paper Trade Simulation
```

---

# ✅ Project Status

## Phase 1 — Real-Time Market Data

* [x] CCXT Pro WebSocket integration
* [x] Binance order book streaming
* [x] Bybit order book streaming
* [x] Kraken order book streaming
* [x] Asynchronous streaming architecture
* [x] Automatic reconnect handling
* [x] Multi-exchange order book caching

## Phase 2 — Order Book Infrastructure

* [x] `OrderBookLevel` data model
* [x] Structured bid/ask representation
* [x] Raw exchange data normalization
* [x] Market depth representation
* [x] Order book access through `.price` and `.amount`

## Phase 3 — Arbitrage Detection

* [x] Cross-exchange scanning
* [x] Bid/ask comparison
* [x] Arbitrage opportunity model
* [x] Opportunity timestamps
* [x] Gross spread calculation
* [x] Net profitability evaluation

## Phase 4 — Profitability & Paper Trading

* [x] Taker fee calculation
* [x] Market-depth evaluation
* [x] Slippage consideration
* [x] Paper trade execution
* [x] Virtual USDT balance
* [x] Trade history tracking

## Phase 5 — Monitoring & Reliability

* [x] System heartbeat logging
* [x] Active order book status
* [x] WebSocket exception handling
* [x] Automatic reconnection
* [x] Graceful shutdown handling

---

# 🐛 Bugs Resolved

During development, several issues were identified and fixed.

### 1. `OrderBookLevel` Object Not Subscriptable

**Error:**

```text
TypeError: 'OrderBookLevel' object is not subscriptable
```

**Cause:**

The arbitrage finder was treating `OrderBookLevel` objects as raw tuples:

```python
asks[0][0]
```

However, the normalized order book uses structured objects.

**Solution:**

The implementation was updated to access the model properties directly:

```python
level.price
level.amount
```

---

### 2. Missing `detected_at` Argument

**Error:**

```text
TypeError: ArbitrageOpportunity.__init__()
missing 1 required positional argument: 'detected_at'
```

**Cause:**

`detected_at` was required when creating an `ArbitrageOpportunity`.

**Solution:**

The dataclass was updated to automatically generate a timestamp:

```python
detected_at: float = field(default_factory=time.time)
```

This allows opportunities to automatically record their detection time.

---

### 3. Silent Evaluation Loop

**Problem:**

The application appeared to stop or freeze when no profitable arbitrage opportunities were detected.

**Cause:**

The evaluation loop did not provide enough status information when market conditions produced no qualifying opportunities.

**Solution:**

Heartbeat logging was added to show active order book feeds:

```text
(3/3: ['bybit', 'binance', 'kraken'])
```

This makes it clear that the system is running even when no arbitrage opportunity currently exists.

---

# 🔬 Current Development Focus

The next development stage focuses on improving market visibility and expanding arbitrage strategies.

## 1. Raw Spread Logging

Add logging to `arbitrage/finder.py` to display raw top-of-book spreads even when the opportunity is not profitable after fees.

Example:

```text
BTC/USDT
Binance → Bybit
Buy: 104250.20
Sell: 104310.50
Gross Spread: 0.0579%
Net Spread: -0.0221%
```

This will help analyze real market behavior and determine how frequently potentially profitable spreads occur.

---

## 2. Configurable Trading Pairs

The system will be extended to support configurable trading pairs.

Example configuration:

```text
BTC/USDT
ETH/USDT
SOL/USDT
DOGE/USDT
PEPE/USDT
```

This will make it possible to test:

* High-liquidity assets
* High-volatility assets
* Low-liquidity assets
* Wider-spread markets
* Different market conditions

---

## 3. Triangular Arbitrage

The next major strategy will introduce **single-exchange triangular arbitrage**.

Example:

```text
BTC
 │
 ▼
ETH
 │
 ▼
USDT
 │
 ▼
BTC
```

The engine will evaluate whether:

```text
BTC → ETH → USDT → BTC
```

produces a positive return after:

* Trading fees
* Price impact
* Market depth
* Slippage

The goal is to build this as a separate strategy module without coupling it tightly to the existing cross-exchange arbitrage engine.

---

# 🗺️ Roadmap

### Market Data

* [x] WebSocket order book streaming
* [x] Multi-exchange support
* [x] Order book normalization
* [x] Reconnection handling
* [ ] Subscription management
* [ ] Connection health metrics

### Arbitrage Detection

* [x] Cross-exchange arbitrage
* [x] Gross spread calculation
* [x] Fee-aware profitability
* [x] Market depth analysis
* [ ] Raw spread monitoring
* [ ] Configurable trading pairs
* [ ] Opportunity ranking
* [ ] Minimum liquidity filters

### Arbitrage Strategies

* [x] Cross-exchange arbitrage foundation
* [ ] Triangular arbitrage
* [ ] Multi-level order book execution
* [ ] Multi-pair scanning
* [ ] Strategy abstraction layer

### Paper Trading

* [x] Virtual balance
* [x] Simulated execution
* [x] Fee calculation
* [x] Trade history
* [ ] Advanced execution simulation
* [ ] Partial-fill simulation
* [ ] Order latency simulation
* [ ] Performance analytics

### Risk Management

* [ ] Maximum trade exposure
* [ ] Maximum daily loss
* [ ] Liquidity thresholds
* [ ] Exchange health checks
* [ ] Position limits
* [ ] Circuit breakers

### Live Trading

* [ ] Exchange API authentication
* [ ] Live order execution
* [ ] Order status tracking
* [ ] Position reconciliation
* [ ] Failure recovery
* [ ] Live risk management

> **Live trading will only be introduced after extensive paper-trading and validation.**

---

# 🧪 Testing

Tests are maintained separately from the production modules.

Run the test suite with:

```powershell
python -m pytest -v
```

Run a specific test file:

```powershell
python -m pytest tests/test_settings.py -v
```

---

# ⚙️ Installation

## Requirements

* Python 3.11+
* CCXT Pro
* WebSocket support
* Internet connection

Clone the repository:

```powershell
git clone <repository-url>
cd ArbiX
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

---

# ▶️ Running ArbiX

Start the application with:

```powershell
python -m main
```

When running successfully, the system periodically reports the status of connected order books.

Example:

```text
INFO - Active order books: 3/3
INFO - Exchanges: ['bybit', 'binance', 'kraken']
```

---

# 🔐 Trading Modes

ArbiX is being developed with a strong separation between simulated and real execution.

```text
┌─────────────────────┐
│      ArbiX          │
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
   PAPER        LIVE
     │           │
     ▼           ▼
Simulation   Real Orders
```

### Paper Mode

Paper mode uses simulated balances and executions.

**No real funds are involved.**

### Live Mode

Live trading is intended for a future phase and will require additional:

* Exchange authentication
* Risk controls
* Order management
* Failure recovery
* Position reconciliation
* Safety validation

---

# ⚠️ Disclaimer

ArbiX is a software engineering and research project.

Cryptocurrency arbitrage involves significant technical and financial risks, including:

* Market volatility
* Slippage
* Network latency
* Exchange downtime
* Liquidity changes
* Order execution failures
* Withdrawal/deposit restrictions
* Fee changes
* API failures

**Paper trading should be thoroughly validated before considering real-money execution.**

---

# 🎯 Project Goals

The long-term goal of ArbiX is to build a modular, scalable arbitrage infrastructure capable of:

```text
Real-Time Market Data
        ↓
Market Normalization
        ↓
Opportunity Detection
        ↓
Profitability Analysis
        ↓
Risk Management
        ↓
Execution Simulation
        ↓
Performance Analytics
        ↓
Validated Live Execution
```

The architecture is intentionally being developed incrementally so that each component can be independently tested, measured, and improved.

---

## 📌 Current Next Step

The immediate development priority is:

```text
1. Raw Spread Logging
        ↓
2. Configurable Trading Pairs
        ↓
3. Low-Liquidity / High-Volatility Testing
        ↓
4. Triangular Arbitrage Engine
        ↓
5. Advanced Paper Trading
        ↓
6. Risk Management
        ↓
7. Live Execution
```

---

## 📄 License

License information will be added as the project approaches its first public release.
