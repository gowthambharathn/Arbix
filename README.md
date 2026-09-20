# 🚀 ArbiX — Real-Time Multi-Exchange Arbitrage Monitor

**ArbiX** is an asynchronous cryptocurrency arbitrage detection system built with Python, `asyncio`, and CCXT Pro.

ArbiX continuously monitors real-time order books across multiple cryptocurrency exchanges and evaluates cross-exchange arbitrage opportunities using executable order-book prices, trading fees, liquidity, and order-book freshness.

The current implementation operates in **Paper Trading / Monitoring Mode** and does not place real trades.

---

## ⚡ Current Features

### ✅ Real-Time Order Book Streaming

ArbiX uses CCXT Pro WebSockets to continuously receive live order-book updates.

Current exchanges:

- Binance
- Bybit
- OKX

Current trading pairs:

- SOL/USDT
- XRP/USDT
- BNB/USDT
- DOGE/USDT
- SUI/USDT

Total configured streams:

```text
5 Symbols × 3 Exchanges = 15 Streams
```

The system has been tested with all **15/15 streams active**.

---

### ✅ Cross-Exchange Arbitrage Detection

ArbiX compares executable prices between different exchanges.

Example:

```text
Buy SOL/USDT on Binance
        ↓
Sell SOL/USDT on Bybit
```

The system evaluates both directions across all configured symbols and exchanges.

---

### ✅ Order-Book Depth Analysis

ArbiX does not rely only on the best bid and best ask.

The system calculates executable prices using multiple order-book levels.

```text
Ask Level 1
Ask Level 2
Ask Level 3
       ↓
Actual Average Buy Price
```

and:

```text
Bid Level 1
Bid Level 2
Bid Level 3
       ↓
Actual Average Sell Price
```

This helps prevent false opportunities caused by insufficient liquidity at the top of the order book.

---

### ✅ Fee-Adjusted Profit Calculation

ArbiX calculates the actual estimated money flow:

```text
Buy Cost
   +
Buy Fee
   ↓
Total Cost

Sell Value
   -
Sell Fee
   ↓
Net Revenue

Net Revenue
   -
Total Cost
   ↓
Net Profit
```

The system calculates:

- Gross spread
- Buy fee
- Sell fee
- Combined fee percentage
- Total cost
- Net revenue
- Net profit
- Net ROI

Example:

```text
Gross Spread:  +0.018%
Fees:          -0.200%
Net Profit:    -$0.181
Net ROI:       -0.181%
```

A positive gross spread is therefore not automatically considered profitable.

---

### ✅ Order-Book Freshness Protection

ArbiX rejects stale order-book data.

Current configuration:

```python
MAX_ORDER_BOOK_AGE_SECONDS = 5.0
```

If either the buy-side or sell-side order book is older than the allowed threshold, the opportunity is ignored.

---

### ✅ Minimum Liquidity Validation

ArbiX verifies that the configured trade amount can be executed using available order-book liquidity.

Current paper trade amount:

```text
$100
```

The system requires sufficient liquidity on both the buy and sell exchanges before considering the opportunity.

---

### ✅ Configurable Trading Parameters

ArbiX supports environment-based configuration through `.env`.

Example:

```env
TRADING_SYMBOLS=SOL/USDT,XRP/USDT,BNB/USDT,DOGE/USDT,SUI/USDT

EXCHANGES=binance,bybit,okx

MIN_PROFIT_PERCENTAGE=0.20

BINANCE_TAKER_FEE=0.001
BYBIT_TAKER_FEE=0.001
OKX_TAKER_FEE=0.001

MAX_TRADE_AMOUNT=100.0
PAPER_BALANCE_USDT=1000.0
```

---

### ✅ Paper Trading Mode

ArbiX currently runs in monitoring/paper mode.

```text
Trading Mode: PAPER
Paper Balance: $1000
Maximum Trade Amount: $100
```

No real orders are submitted to exchanges.

---

### ✅ Live CLI Dashboard

ArbiX provides a continuously updating terminal dashboard.

Example:

```text
======================================================================
 ARBIX LIVE MONITORING | Active Streams: 15/15
======================================================================
SYMBOL     | BUY AT   | SELL AT  | BEST SPREAD  | NET PROFIT
----------------------------------------------------------------------
SOL/USDT   | binance  | bybit    | +0.018%      | -0.181%
BNB/USDT   | binance  | bybit    | +0.009%      | -0.190%
XRP/USDT   | N/A      | N/A      | Waiting data | N/A
DOGE/USDT  | N/A      | N/A      | Waiting data | N/A
SUI/USDT   | N/A      | N/A      | Waiting data | N/A
======================================================================
Target Profit Threshold: >=0.2% (Listening for opportunities...)
======================================================================
```

---

# 🏗️ Architecture

```text
ArbiX/
│
├── arbitrage/
│   ├── __init__.py
│   └── finder.py
│       └── Arbitrage calculation engine
│
├── config/
│   ├── __init__.py
│   └── settings.py
│       └── Application configuration
│
├── market_data/
│   ├── __init__.py
│   ├── order_book.py
│   │   └── Normalized order-book models
│   │
│   └── streamer.py
│       └── CCXT Pro WebSocket streams
│
├── main.py
│   └── Application entry point and monitoring loop
│
├── requirements.txt
│   └── Python dependencies
│
├── .env
│   └── Local configuration
│
└── README.md
```

---

# 🔄 Arbitrage Detection Pipeline

```text
Exchange WebSocket Streams
            ↓
      Live Order Books
            ↓
      Order Book Validation
            ↓
      Freshness Check
            ↓
      Liquidity Check
            ↓
   Order Book Depth Analysis
            ↓
   Executable Buy Price
            +
   Executable Sell Price
            ↓
      Trading Fees
            ↓
       Net Profit
            ↓
     Net ROI Calculation
            ↓
   Profit Threshold Check
            ↓
      CLI Dashboard
```

---

# ⚙️ Current Configuration

### Exchanges

```text
Binance
Bybit
OKX
```

### Symbols

```text
SOL/USDT
XRP/USDT
BNB/USDT
DOGE/USDT
SUI/USDT
```

### Trading Mode

```text
PAPER
```

### Minimum Net Profit

```text
0.20%
```

### Maximum Trade Amount

```text
$100
```

### Paper Balance

```text
$1000
```

### Maximum Order-Book Age

```text
5 seconds
```

---

# 🧪 Validation Status

The current system has been tested successfully with:

```text
Binance   → Connected
Bybit     → Connected
OKX       → Connected

SOL/USDT  → Working
XRP/USDT  → Working
BNB/USDT  → Working
DOGE/USDT → Working
SUI/USDT  → Working
```

Current verified stream capacity:

```text
15 / 15 Active Streams
```

ArbiX is successfully receiving live market data from all configured exchange/symbol combinations.

---

# 🛠️ Development Progress

## ✅ Completed

- [x] Project architecture
- [x] Async application structure
- [x] CCXT Pro integration
- [x] Binance market streaming
- [x] Bybit market streaming
- [x] OKX market streaming
- [x] Multi-symbol support
- [x] Multi-exchange support
- [x] Normalized order-book model
- [x] Best bid / best ask calculation
- [x] Order-book depth calculation
- [x] Executable average buy price
- [x] Executable average sell price
- [x] Cross-exchange spread detection
- [x] Buy-side fee calculation
- [x] Sell-side fee calculation
- [x] Net profit calculation
- [x] Net ROI calculation
- [x] Order-book freshness protection
- [x] Minimum liquidity validation
- [x] Configurable trading symbols
- [x] Configurable exchanges
- [x] Configurable exchange fees
- [x] Configurable profit threshold
- [x] Configurable trade amount
- [x] Paper trading configuration
- [x] Live CLI monitoring dashboard
- [x] 15/15 stream validation

---

# 🚧 Development Roadmap

## 🔄 Step 4 — Slippage Protection

Add explicit slippage limits to reject opportunities where the executable average price moves too far away from the best available price.

Planned protection:

```text
Best Ask
   ↓
Average Buy Price
   ↓
Calculate Buy Slippage

Best Bid
   ↓
Average Sell Price
   ↓
Calculate Sell Slippage
```

Opportunities exceeding the configured slippage limit will be rejected.

**Status:** 🔄 In Progress

---

## ⏳ Step 5 — Accurate Trade Sizing

Improve trade-size calculation so the requested trade amount remains within the configured budget even when order-book depth causes execution prices to move.

Current approach:

```text
Trade Quantity
=
Trade Amount / Best Ask
```

Planned approach:

```text
Maximum Trade Budget
        ↓
Fees + Order Book Depth
        ↓
Exact Executable Quantity
        ↓
Final Trade Cost
```

**Status:** ⏳ Planned

---

## ⏳ Step 6 — Paper Execution Engine

Build a complete paper-trading execution engine.

It will simulate:

```text
BUY
 ↓
Asset acquired
 ↓
SELL
 ↓
Profit / Loss
 ↓
Paper balance updated
```

The system will maintain simulated balances and trade history.

**Status:** ⏳ Planned

---

## ⏳ Step 7 — Risk Management

Introduce additional risk controls such as:

- Maximum trades per period
- Maximum daily loss
- Maximum exposure
- Maximum concurrent opportunities
- Cooldown after failed execution
- Exchange-specific limits
- Opportunity timeout

**Status:** ⏳ Planned

---

## ⏳ Step 8 — Execution Safety Checks

Before any future live execution, ArbiX will validate:

- Order-book freshness
- Available liquidity
- Expected slippage
- Trading fees
- Trade size
- Exchange connectivity
- Balance availability
- Market status
- Minimum profit after costs

**Status:** ⏳ Planned

---

## ⏳ Step 9 — Live Trading Engine

A future live-trading module may support actual order execution.

Planned architecture:

```text
Opportunity Detector
        ↓
Risk Manager
        ↓
Execution Validator
        ↓
Exchange Order
        ↓
Execution Confirmation
        ↓
Second Exchange Order
        ↓
Position Reconciliation
```

Live trading will remain disabled until the paper-trading and risk-management layers are validated.

**Status:** ⏳ Future

---

# ⚠️ Important Limitations

ArbiX currently detects executable arbitrage opportunities from live order books, but detection does not guarantee that a real trade can be completed at the calculated prices.

Real execution can be affected by:

- Market movement
- Network latency
- WebSocket latency
- Order-book changes
- Slippage
- Exchange fees
- Order execution delays
- Partial fills
- Minimum order sizes
- Exchange-specific precision
- Withdrawal/deposit restrictions
- Asset availability
- Transfer delays
- API/exchange outages

Therefore:

```text
Detected Opportunity
        ≠
Guaranteed Profit
```

The current system is intentionally limited to **paper/monitoring mode**.

---

# 🚀 Getting Started

## 1. Requirements

Recommended:

```text
Python 3.10+
```

Tested with:

```text
Python 3.12
Python 3.14
```

A virtual environment is recommended.

---

## 2. Create Virtual Environment

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment

Create a `.env` file in the project root:

```env
TRADING_SYMBOLS=SOL/USDT,XRP/USDT,BNB/USDT,DOGE/USDT,SUI/USDT
EXCHANGES=binance,bybit,okx

MIN_PROFIT_PERCENTAGE=0.20

BINANCE_TAKER_FEE=0.001
BYBIT_TAKER_FEE=0.001
OKX_TAKER_FEE=0.001

MAX_TRADE_AMOUNT=100.0
PAPER_BALANCE_USDT=1000.0
```

The fee values should be configured according to the actual trading fee tier applicable to the exchange account before using the calculations for real trading decisions.

---

## 5. Run ArbiX

From the project root:

```powershell
python -m main
```

---

# 📊 Example Monitoring Output

```text
======================================================================
 ARBIX LIVE MONITORING | Active Streams: 15/15
======================================================================
SYMBOL     | BUY AT   | SELL AT  | BEST SPREAD  | NET PROFIT
----------------------------------------------------------------------
SOL/USDT   | binance  | bybit    | +0.018%      | -0.181%
BNB/USDT   | binance  | bybit    | +0.009%      | -0.190%
======================================================================
Target Profit Threshold: >=0.2% (Listening for opportunities...)
======================================================================
```

A negative net profit despite a positive gross spread is expected when the spread is smaller than the combined trading costs.

---

# 🧠 Design Philosophy

ArbiX is being developed incrementally with an emphasis on:

```text
Real-Time Data
      +
Accurate Execution Pricing
      +
Trading Costs
      +
Liquidity
      +
Freshness
      +
Slippage Protection
      +
Risk Management
      ↓
Reliable Arbitrage Detection
```

The project prioritizes **correctness and execution realism** before introducing live trading.

---

# 📜 License

Distributed under the MIT License.

See `LICENSE` for details.
