# Laakhay TA

**Professional, stateless technical analysis library for cryptocurrency markets.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Philosophy

**Data-Source Agnostic by Design**

Laakhay TA is built on a simple principle: *technical indicators shouldn't care where data comes from*. 

- ✅ Works with **any data provider** (Binance, Coinbase, your own database, CSV files)
- ✅ **Truly stateless** - no hidden state, no global variables, no side effects
- ✅ **Pure functional** - same input always produces same output
- ✅ **Composable** - indicators can depend on other indicators
- ✅ **Type-safe** - full Pydantic validation and Python type hints

## 🚀 Quick Start

### Installation

```bash
pip install laakhay-ta
```

### Basic Usage

```python
from datetime import datetime
from decimal import Decimal
from laakhay.ta.models import Candle
from laakhay.ta.core import TAInput

# Create candle data from ANY source
candles = [
    Candle(
        symbol="BTCUSDT",
        timestamp=datetime(2024, 1, 1, 0, 0),
        open=Decimal("42000"),
        high=Decimal("42500"),
        low=Decimal("41800"),
        close=Decimal("42300"),
        volume=Decimal("100.5"),
        is_closed=True,
    ),
    # ... more candles
]

# Prepare input for indicators
ta_input = TAInput(
    candles={"BTCUSDT": candles},
    scope_symbols=["BTCUSDT"],
)

# Use any indicator (examples coming soon)
# result = SomeIndicator.compute(ta_input, period=14)
```

## 📦 Data Models

Laakhay TA defines simple, immutable data models that any data source can implement:

### Core Models

#### `Candle` - OHLCV Price Data
```python
from laakhay.ta.models import Candle

candle = Candle(
    symbol="BTCUSDT",
    timestamp=datetime.now(),
    open=Decimal("42000"),
    high=Decimal("42500"),
    low=Decimal("41800"),
    close=Decimal("42300"),
    volume=Decimal("100.5"),
    is_closed=True,
)

# Built-in helpers
print(candle.hlc3)  # Typical price
print(candle.ohlc4)  # Average price
print(candle.is_fresh(max_age_seconds=120))  # Data freshness check
```

#### `OpenInterest` - Futures Open Interest
```python
from laakhay.ta.models import OpenInterest

oi = OpenInterest(
    symbol="BTCUSDT",
    timestamp=datetime.now(),
    open_interest=Decimal("50000"),
    open_interest_value=Decimal("2100000000"),  # Optional
)
```

#### `FundingRate` - Perpetual Futures Funding
```python
from laakhay.ta.models import FundingRate

funding = FundingRate(
    symbol="BTCUSDT",
    funding_time=datetime.now(),
    funding_rate=Decimal("0.0001"),
    mark_price=Decimal("42000"),  # Optional
)

print(funding.funding_rate_percentage)  # 0.01%
print(funding.annual_rate_percentage)   # Annualized rate
print(funding.is_positive)              # Longs pay shorts?
```

#### `MarkPrice` - Mark/Index Price Data
```python
from laakhay.ta.models import MarkPrice

mark = MarkPrice(
    symbol="BTCUSDT",
    mark_price=Decimal("42000"),
    index_price=Decimal("41995"),  # Optional
    timestamp=datetime.now(),
)

print(mark.mark_index_spread_bps)  # Spread in basis points
print(mark.is_premium)              # Trading at premium?
print(mark.spread_severity)         # "normal", "moderate", "high", "extreme"
```

## 🏗️ Architecture

### Stateless Indicator Design

```python
from laakhay.ta.core import BaseIndicator, TAInput, TAOutput
from laakhay.ta.core.spec import IndicatorRequirements, RawDataRequirement, WindowSpec

class MyIndicator(BaseIndicator):
    """Example indicator - completely stateless."""
    
    name = "my_indicator"
    kind = "batch"  # or "stream"
    
    @classmethod
    def requirements(cls) -> IndicatorRequirements:
        """Declare what data this indicator needs."""
        return IndicatorRequirements(
            raw=[
                RawDataRequirement(
                    kind="price",
                    price_field="close",
                    window=WindowSpec(lookback_bars=20),
                    only_closed=True,
                )
            ]
        )
    
    @classmethod
    def compute(cls, input: TAInput, **params) -> TAOutput:
        """Pure computation - no side effects, no state."""
        # Your indicator logic here
        results = {}
        for symbol in input.scope_symbols:
            candles = input.candles[symbol]
            # ... compute indicator value
            results[symbol] = some_value
        
        return TAOutput(
            name=cls.name,
            values=results,
            ts=input.eval_ts,
        )
```

### Key Principles

1. **No Instances** - All indicator methods are class methods
2. **No State** - No instance variables, no class variables (except config)
3. **Declarative Dependencies** - Requirements specified upfront
4. **Deterministic** - Same input always produces same output
5. **Composable** - Indicators can depend on other indicators

## 🔌 Integrating Your Data Source

To use Laakhay TA with your data source, simply convert your data to `Candle` objects:

### Example: CSV File
```python
import csv
from datetime import datetime
from decimal import Decimal
from laakhay.ta.models import Candle

def load_candles_from_csv(filepath: str) -> list[Candle]:
    candles = []
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            candles.append(Candle(
                symbol=row['symbol'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                open=Decimal(row['open']),
                high=Decimal(row['high']),
                low=Decimal(row['low']),
                close=Decimal(row['close']),
                volume=Decimal(row['volume']),
                is_closed=True,
            ))
    return candles
```

### Example: Database
```python
from laakhay.ta.models import Candle

def load_candles_from_db(symbol: str, start: datetime, end: datetime) -> list[Candle]:
    # Your database query here
    rows = db.execute(
        "SELECT * FROM candles WHERE symbol = ? AND timestamp BETWEEN ? AND ?",
        (symbol, start, end)
    )
    
    return [
        Candle(
            symbol=row['symbol'],
            timestamp=row['timestamp'],
            open=Decimal(str(row['open'])),
            high=Decimal(str(row['high'])),
            low=Decimal(str(row['low'])),
            close=Decimal(str(row['close'])),
            volume=Decimal(str(row['volume'])),
            is_closed=True,
        )
        for row in rows
    ]
```

### Example: REST API
```python
import requests
from laakhay.ta.models import Candle

def load_candles_from_api(symbol: str) -> list[Candle]:
    response = requests.get(f"https://api.example.com/candles?symbol={symbol}")
    data = response.json()
    
    return [
        Candle(
            symbol=item['symbol'],
            timestamp=datetime.fromtimestamp(item['timestamp'] / 1000),
            open=Decimal(item['open']),
            high=Decimal(item['high']),
            low=Decimal(item['low']),
            close=Decimal(item['close']),
            volume=Decimal(item['volume']),
            is_closed=True,
        )
        for item in data
    ]
```

## 🎓 Why Stateless?

Traditional TA libraries (like TA-Lib) maintain internal state, making them:
- ❌ Hard to test
- ❌ Difficult to parallelize
- ❌ Prone to subtle bugs
- ❌ Cannot backtest reliably

Laakhay TA is **truly stateless**:
- ✅ Every computation is independent
- ✅ Perfect for parallel processing
- ✅ Easy to test and debug
- ✅ Reliable backtesting
- ✅ No hidden state = no surprises

## 🛣️ Roadmap

### Phase 1: Core Framework (Current)
- [x] Data models
- [x] Stateless indicator contract
- [x] Registry system
- [x] Dependency declaration
- [ ] Execution engine
- [ ] Cycle detection

### Phase 2: Indicator Library
- [ ] Trend indicators (SMA, EMA, MACD, etc.)
- [ ] Momentum indicators (RSI, Stochastic, etc.)
- [ ] Volume indicators (OBV, VWAP, etc.)
- [ ] Volatility indicators (ATR, Bollinger Bands, etc.)

### Phase 3: Advanced Features
- [ ] Async execution support
- [ ] Distributed caching
- [ ] Stream processing
- [ ] Plan optimization
- [ ] Visualization tools

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- **laakhay-data** - Data aggregation library (optional companion)
- **crypto-alerts-backend** - Real-time alerting system using laakhay-ta

## 💬 Support

- 📧 Email: team@laakhay.com
- 🐛 Issues: [GitHub Issues](https://github.com/laakhay/api.laakhay.com/issues)
- 📖 Docs: [docs.laakhay.com/ta](https://docs.laakhay.com/ta)

---

Built with ♥︎ by [Laakhay](https://laakhay.com)
