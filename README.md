# 🚀 ArbiX - Real-Time Multi-Exchange Arbitrage Monitor

**ArbiX** is an asynchronous, high-frequency cryptocurrency arbitrage detection bot built with Python and `asyncio`. It streams real-time L2/L3 order book data across multiple exchanges, continuously calculating order book spreads, fee-adjusted net profits, and cross-exchange arbitrage opportunities.

---

## ⚡ Features

* **Real-Time Order Book Streaming**: Non-blocking asynchronous order book data updates using `asyncio`.
* **Fee-Adjusted Net Spreads**: Automatically calculates gross spreads and deducts exchange taker fees to verify real profit margins.
* **Dynamic Configuration Handling**: Flexible configuration bindings for exchange pairs, base assets, and minimum profit thresholds.
* **Robust Type Handling**: Converts raw stream `OrderBookLevel` objects into structured numerical calculations seamlessly.
* **Live CLI Dashboard**: Real-time terminal output displaying active streams, current best bid/ask, and highest spread opportunities.

---

## 📂 Project Structure

```text
ArbiX/
├── arbitrage/
│   ├── __init__.py
│   └── finder.py        # Spreads evaluation & arbitrage calculation engine
│
├── config/
│   ├── __init__.py
│   └── settings.py      # Fee structures, exchange pairs, and target thresholds
│
├── market_data/
│   ├── __init__.py
│   ├── models.py        # Order book data structures & level models
│   └── streamer.py      # Async exchange stream connector
│
├── README.md            # Project documentation
└── main.py              # Main execution loop & live dashboard
```

---

## 🚀 Getting Started

### 1. Prerequisites

* **Python**: Version `3.10+` (Tested on Python 3.12 / 3.14)
* **Virtual Environment** (Recommended)

---

### 2. Installation

1. Clone or navigate to your project directory:

```bash
cd C:\Development\Software\Infinity\Ai\ArbiX
```

2. Create and activate a virtual environment (optional but recommended):

#### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### Linux/macOS

```bash
python -m venv venv
source venv/bin/activate
```

3. Install required dependencies:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

Update `config/settings.py` to customize symbols, default exchanges, and profit margins:

```python
# Default Trading Parameters
DEFAULT_EXCHANGES = ["binance", "kraken", "bybit"]
DEFAULT_SYMBOLS = ["BTC/USDT", "SOL/USDT", "DOGE/USDT", "PEPE/USDT"]

# Arbitrage Thresholds
MIN_PROFIT_PERCENTAGE = 0.20        # Minimum net profit % required to trigger alert
TOTAL_TAKER_FEE_PERCENTAGE = 0.20   # Combined fee estimate (Buy Taker + Sell Taker)
```

---

## 🏃 Execution

Run the project module using standard Python execution from the root directory:

```bash
python -m main
```

---

## 📊 Live Monitoring View

Once running, the live dashboard auto-refreshes every few seconds:

```text
======================================================================
 🚀 ARBIX LIVE MONITORING | Active Streams: 11/12
======================================================================

SYMBOL     | BUY AT   | SELL AT  | BEST SPREAD  | NET PROFIT
----------------------------------------------------------------------
BTC/USDT   | binance  | kraken   | +0.082%      | -0.118%
SOL/USDT   | bybit    | binance  | +0.412%      | 🔥 YES
DOGE/USDT  | kraken   | bybit    | -0.015%      | -0.215%
PEPE/USDT  | binance  | bybit    | +0.030%      | -0.170%

======================================================================
Target Profit Threshold: >=0.2% (Listening for opportunities...)
======================================================================
```

---

## 🛡️ License

Distributed under the MIT License. See `LICENSE` for details.
