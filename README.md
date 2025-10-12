# Laakhay TA

**Production-ready technical analysis library for cryptocurrency markets.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Philosophy

**Stateless. Efficient. Battle-tested.**

Laakhay TA is built on three core principles:

1. **Data-Source Agnostic** - Works with any data provider (Binance, your DB, CSV files)
2. **Truly Stateless** - Pure functional design, no hidden state, deterministic
3. **Series-First** - Returns complete time series for efficient backtesting

Unlike traditional TA libraries that maintain internal state and return single values, Laakhay TA computes entire series in one pass—perfect for backtesting and analysis.

## 🚀 Quick Start

### Installation

```bash
pip install laakhay-ta
```

### Simple Example

```python
from datetime import datetime, timezone
from decimal import Decimal
from laakhay.ta.models import Candle
from laakhay.ta.core.plan import ComputeRequest, build_execution_plan, execute_plan

# 1. Create candle data (from ANY source)
candles = [
    Candle(
        symbol="BTCUSDT",
        timestamp=datetime(2024, 1, 1, i, 0, tzinfo=timezone.utc),
        open=Decimal(str(42000 + i * 10)),
        high=Decimal(str(42100 + i * 10)),
        low=Decimal(str(41900 + i * 10)),
        close=Decimal(str(42050 + i * 10)),
        volume=Decimal("100.5"),
        is_closed=True,
    )
    for i in range(50)
]

# 2. Create compute request
request = ComputeRequest(
    indicator_name="rsi",
    params={"period": 14},
    symbols=["BTCUSDT"],
    eval_ts=candles[-1].timestamp,
)

# 3. Build execution plan (handles dependencies automatically)
plan = build_execution_plan(request)

# 4. Provide data
raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}

# 5. Execute and get results
result = execute_plan(plan, raw_cache, request)

# 6. Access time series
rsi_series = result.values["BTCUSDT"]  # [(timestamp, rsi_value), ...]
latest_rsi = rsi_series[-1][1]
print(f"Latest RSI: {latest_rsi:.2f}")
```

## 📊 Available Indicators

### ✅ Trend Indicators
- **SMA** - Simple Moving Average
- **EMA** - Exponential Moving Average
- **Bollinger Bands** - Volatility bands with SMA

### ✅ Momentum Indicators
- **RSI** - Relative Strength Index (Wilder's smoothing)
- **MACD** - Moving Average Convergence Divergence
- **Stochastic** - Stochastic Oscillator (%K and %D)

### ✅ Volume Indicators
- **VWAP** - Volume Weighted Average Price (cumulative & rolling)

### ✅ Volatility Indicators
- **ATR** - Average True Range (Wilder's smoothing)
- **Bollinger Bands** - Standard deviation bands

### ✅ Analytics & Signals
- **Correlation** - Inter-asset correlation (Pearson)
- **Relative Strength** - Performance vs benchmark
- **Volume Analysis** - Multi-window spike detection
- **Statistics** - Returns, volatility, Sharpe ratio
- **Spike Detection** - Price & volume spike algorithms

**All indicators:**
- ✅ Return complete time series (not just latest value)
- ✅ Tested with manual calculations (accuracy < 1e-10)
- ✅ Support configurable parameters
- ✅ Include comprehensive docstrings

## 📚 Detailed Examples

## � Detailed Examples

### RSI with Overbought/Oversold Signals

```python
from laakhay.ta.core.plan import ComputeRequest, build_execution_plan, execute_plan

# Compute RSI
request = ComputeRequest(
    indicator_name="rsi",
    params={"period": 14, "price_field": "close"},
    symbols=["BTCUSDT"],
    eval_ts=candles[-1].timestamp,
)

plan = build_execution_plan(request)
raw_cache = {("raw", "price", "close", "BTCUSDT"): candles}
result = execute_plan(plan, raw_cache, request)

# Analyze signals
rsi_series = result.values["BTCUSDT"]
for timestamp, rsi_value in rsi_series[-10:]:  # Last 10 values
    if rsi_value > 70:
        print(f"{timestamp}: RSI {rsi_value:.2f} - OVERBOUGHT")
    elif rsi_value < 30:
        print(f"{timestamp}: RSI {rsi_value:.2f} - OVERSOLD")
```

### MACD Crossover Strategy

```python
# Compute MACD
request = ComputeRequest(
    indicator_name="macd",
    params={"fast": 12, "slow": 26, "signal": 9},
    symbols=["BTCUSDT", "ETHUSDT"],
    eval_ts=candles[-1].timestamp,
)

result = execute_plan(build_execution_plan(request), raw_cache, request)

# Check for crossovers
for symbol in ["BTCUSDT", "ETHUSDT"]:
    macd_data = result.values[symbol]
    
    # Latest values
    _, latest_macd = macd_data["macd"][-1]
    _, latest_signal = macd_data["signal"][-1]
    _, latest_hist = macd_data["histogram"][-1]
    
    # Previous values
    _, prev_hist = macd_data["histogram"][-2]
    
    # Detect crossover
    if prev_hist < 0 and latest_hist > 0:
        print(f"{symbol}: Bullish crossover! MACD crossed above signal")
    elif prev_hist > 0 and latest_hist < 0:
        print(f"{symbol}: Bearish crossover! MACD crossed below signal")
```

### Bollinger Bands Squeeze Detection

```python
# Compute Bollinger Bands
request = ComputeRequest(
    indicator_name="bbands",
    params={"period": 20, "num_std": 2.0},
    symbols=["BTCUSDT"],
    eval_ts=candles[-1].timestamp,
)

result = execute_plan(build_execution_plan(request), raw_cache, request)
bb_data = result.values["BTCUSDT"]

# Calculate bandwidth
bandwidths = []
for i in range(len(bb_data["upper"])):
    upper_val = bb_data["upper"][i][1]
    lower_val = bb_data["lower"][i][1]
    middle_val = bb_data["middle"][i][1]
    
    # Bandwidth as percentage of middle band
    bandwidth_pct = ((upper_val - lower_val) / middle_val) * 100
    bandwidths.append(bandwidth_pct)

# Detect squeeze (narrowing bands = low volatility)
if bandwidths[-1] < 5.0:  # Less than 5% bandwidth
    print("⚠️  Bollinger Bands SQUEEZE detected - breakout imminent!")
```

### Multi-Indicator Confluence

```python
# Combine RSI + Stochastic + MACD for strong signals
from laakhay.ta.core.plan import ComputeRequest, build_execution_plan, execute_plan

def get_trading_signals(candles, symbol):
    """Get confluence signals from multiple indicators."""
    
    # Compute RSI
    rsi_req = ComputeRequest("rsi", {"period": 14}, [symbol], candles[-1].timestamp)
    rsi_result = execute_plan(
        build_execution_plan(rsi_req),
        {("raw", "price", "close", symbol): candles},
        rsi_req
    )
    rsi = rsi_result.values[symbol][-1][1]
    
    # Compute Stochastic
    stoch_req = ComputeRequest("stoch", {"k_period": 14, "d_period": 3}, [symbol], candles[-1].timestamp)
    stoch_result = execute_plan(
        build_execution_plan(stoch_req),
        {("raw", "price", "close", symbol): candles},
        stoch_req
    )
    stoch_k = stoch_result.values[symbol]["k"][-1][1]
    
    # Compute MACD
    macd_req = ComputeRequest("macd", {}, [symbol], candles[-1].timestamp)
    macd_result = execute_plan(
        build_execution_plan(macd_req),
        {("raw", "price", "close", symbol): candles},
        macd_req
    )
    macd_hist = macd_result.values[symbol]["histogram"][-1][1]
    
    # Confluence signals
    bullish_signals = 0
    bearish_signals = 0
    
    if rsi < 30:
        bullish_signals += 1
    elif rsi > 70:
        bearish_signals += 1
    
    if stoch_k < 20:
        bullish_signals += 1
    elif stoch_k > 80:
        bearish_signals += 1
    
    if macd_hist > 0:
        bullish_signals += 1
    elif macd_hist < 0:
        bearish_signals += 1
    
    # Strong signal = 2+ indicators agree
    if bullish_signals >= 2:
        return "STRONG BUY"
    elif bearish_signals >= 2:
        return "STRONG SELL"
    else:
        return "NEUTRAL"

signal = get_trading_signals(candles, "BTCUSDT")
print(f"Trading Signal: {signal}")
```

### VWAP as Support/Resistance

```python
# Compute VWAP
request = ComputeRequest(
    indicator_name="vwap",
    params={"price_field": "hlc3"},  # Typical price
    symbols=["BTCUSDT"],
    eval_ts=candles[-1].timestamp,
)

result = execute_plan(build_execution_plan(request), raw_cache, request)
vwap_series = result.values["BTCUSDT"]

# Compare price to VWAP
latest_close = float(candles[-1].close)
_, latest_vwap = vwap_series[-1]

if latest_close > latest_vwap:
    premium_pct = ((latest_close - latest_vwap) / latest_vwap) * 100
    print(f"Price is {premium_pct:.2f}% ABOVE VWAP (resistance)")
else:
    discount_pct = ((latest_vwap - latest_close) / latest_vwap) * 100
    print(f"Price is {discount_pct:.2f}% BELOW VWAP (support)")
```

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

### Phase 1: Core Framework ✅ **COMPLETE**
- [x] Data models (Candle, OpenInterest, FundingRate, MarkPrice)
- [x] Stateless indicator contract
- [x] Registry system
- [x] Dependency declaration
- [x] Execution engine with DAG resolution
- [x] Cycle detection

### Phase 2: Indicator Library ✅ **80% COMPLETE**
- [x] **Trend:** SMA, EMA, Bollinger Bands
- [x] **Momentum:** RSI, MACD, Stochastic, EMA
- [x] **Volume:** VWAP
- [x] **Volatility:** ATR, Bollinger Bands
- [ ] **Advanced:** ADX, Ichimoku, Parabolic SAR, Supertrend
- [ ] **Additional Volume:** OBV, MFI

### Phase 3: Production Features (In Progress)
- [x] Series-based output for efficiency
- [x] Comprehensive testing methodology
- [x] Professional documentation
- [ ] PyPI packaging
- [ ] Integration adapters (laakhay-data)
- [ ] Real-world examples

### Phase 4: Advanced Features
- [ ] Streaming indicators (real-time updates)
- [ ] Async execution support
- [ ] Distributed caching
- [ ] Plan optimization
- [ ] Visualization tools
- [ ] Multi-timeframe analysis

## 📖 Indicator Reference

### SMA (Simple Moving Average)
**Category:** Trend | **Module:** `laakhay.ta.indicators.trend`

**Parameters:**
- `period` (int, default=20): Number of bars to average
- `price_field` (str, default="close"): open/high/low/close/hlc3/ohlc4/hl2

**Use Cases:** Trend identification, support/resistance, golden cross/death cross

---

### EMA (Exponential Moving Average)
**Category:** Momentum | **Module:** `laakhay.ta.indicators.momentum`

**Parameters:**
- `period` (int, default=20): EMA period
- `price_field` (str, default="close")

**Formula:** EMA = price × α + prev_EMA × (1-α), α = 2/(period+1)

**Use Cases:** Faster trend following, MACD foundation

---

### RSI (Relative Strength Index)
**Category:** Momentum Oscillator | **Module:** `laakhay.ta.indicators.momentum`

**Parameters:**
- `period` (int, default=14): Lookback period
- `price_field` (str, default="close")

**Range:** 0-100 | **Overbought:** >70 | **Oversold:** <30

**Use Cases:** Overbought/oversold, divergence, trend strength

---

### MACD (Moving Average Convergence Divergence)
**Category:** Trend-Following Momentum | **Module:** `laakhay.ta.indicators.momentum`

**Parameters:**
- `fast` (int, default=12), `slow` (int, default=26), `signal` (int, default=9)

**Returns:** `{"macd": [...], "signal": [...], "histogram": [...]}`

**Use Cases:** Crossover signals, divergence, trend strength

---

### Stochastic Oscillator
**Category:** Momentum Oscillator | **Module:** `laakhay.ta.indicators.momentum`

**Parameters:**
- `k_period` (int, default=14), `d_period` (int, default=3), `smooth_k` (int, default=1)

**Returns:** `{"k": [...], "d": [...]}`

**Range:** 0-100 | **Overbought:** >80 | **Oversold:** <20

**Use Cases:** Overbought/oversold, crossover signals, divergence

---

### ATR (Average True Range)
**Category:** Volatility | **Module:** `laakhay.ta.indicators.volatility`

**Parameters:**
- `period` (int, default=14): Smoothing period

**Use Cases:** Volatility measurement, position sizing, stop-loss placement

---

### Bollinger Bands
**Category:** Volatility + Trend | **Module:** `laakhay.ta.indicators.volatility`

**Parameters:**
- `period` (int, default=20), `num_std` (float, default=2.0), `price_field` (str, default="close")

**Returns:** `{"upper": [...], "middle": [...], "lower": [...]}`

**Use Cases:** Volatility visualization, squeeze patterns, mean reversion

---

### VWAP (Volume Weighted Average Price)
**Category:** Volume | **Module:** `laakhay.ta.indicators.volume`

**Parameters:**
- `price_field` (str, default="hlc3"), `window` (int, optional)

**Formula:** Σ(Price × Volume) / Σ(Volume)

**Use Cases:** Fair value, support/resistance, institutional benchmark

---

## 🧮 Analytics Module

**Purpose**: Stateless market analysis for cross-asset operations. Unlike indicators (single-symbol, DAG-resolved), analytics handle multi-symbol comparisons, screening, and statistical operations.

### Correlation Analysis

```python
from laakhay.ta.analytics import CorrelationAnalyzer

# Calculate correlation between ETH and BTC
result = CorrelationAnalyzer.correlate_candle_series(
    symbol_candles=eth_candles,
    base_candles=btc_candles,
    price_field="close"
)

print(f"Correlation: {result.coefficient:.2f}")
print(f"Strength: {result.strength}")  # weak/moderate/strong/very_strong

# Rolling correlation
series = CorrelationAnalyzer.rolling_correlation_series(
    symbol_candles=eth_candles,
    base_candles=btc_candles,
    window_size=20
)
```

**Use Cases**: Pair trading, risk management, market regime detection

---

### Relative Strength Analysis

```python
from laakhay.ta.analytics import RelativeStrengthAnalyzer

# Compare ETH vs BTC performance
result = RelativeStrengthAnalyzer.calculate_relative_strength(
    symbol_start=Decimal("2000"),
    symbol_end=Decimal("2100"),
    base_start=Decimal("40000"),
    base_end=Decimal("41000")
)

print(f"RS: {result.relative_strength:.2f}%")  # 2.5% (outperforming)
print(f"Category: {result.strength_category}")  # outperform

# Rank multiple assets
ranked = RelativeStrengthAnalyzer.rank_by_relative_strength(
    symbol_candles_map={
        "ETHUSDT": eth_candles,
        "BNBUSDT": bnb_candles,
        "SOLUSDT": sol_candles
    },
    base_candles=btc_candles,
    top_n=5
)
```

**Use Cases**: Asset screening, rotation strategies, divergence detection

---

### Volume Analysis

```python
from laakhay.ta.analytics import VolumeAnalyzer

# Multi-window volume analysis
results = VolumeAnalyzer.analyze_volume_vs_baselines(
    current_volume=Decimal("1000000"),
    candles=historical_candles,
    windows={"short": 20, "medium": 100, "long": 1000}
)

for name, analysis in results.items():
    print(f"{name}: {analysis.multiplier:.1f}x baseline")
    print(f"  Z-score: {analysis.zscore:.2f}")
    print(f"  Percentile: {analysis.percentile:.1f}%")
```

**Use Cases**: Volume spike detection, anomaly detection, breakout confirmation

---

### Statistical Utilities

```python
from laakhay.ta.analytics import StatisticalUtils

# Calculate returns
prices = [Decimal("100"), Decimal("105"), Decimal("110")]
log_returns = StatisticalUtils.calculate_returns(prices, method="log")
pct_returns = StatisticalUtils.calculate_returns(prices, method="pct")

# Volatility (annualized)
vol = StatisticalUtils.calculate_volatility(returns, annualization_factor=252)

# Sharpe ratio
sharpe = StatisticalUtils.calculate_sharpe_ratio(
    returns,
    risk_free_rate=0.02,
    annualization_factor=252
)

# Percentile rank & z-score
percentile = StatisticalUtils.percentile_rank(102.5, [100, 101, 102, 103, 104])
zscore = StatisticalUtils.zscore(110, [100, 102, 104, 106, 108])
```

**Use Cases**: Portfolio analytics, risk metrics, performance attribution

---

### Spike Detection

```python
from laakhay.ta.signals import PriceSpikeDetector, VolumeSpikeDetector

# Price spike detection
spike_result = PriceSpikeDetector.detect_spike(candle)
if spike_result.is_spike:
    print(f"{spike_result.direction} spike: {spike_result.spike_pct}%")
    print(f"Strength: {spike_result.strength}")  # weak/moderate/strong/extreme

# Volume spike detection
vol_result = VolumeSpikeDetector.detect_volume_spike(
    candle=current_candle,
    historical_candles=candles[:-1],
    multiplier_threshold=2.0
)
```

**Use Cases**: Real-time alerts, breakout detection, anomaly monitoring

---

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
