# Laakhay-TA

A composable technical analysis library with immutable data structures and expression-based indicator composition.

## Overview

Laakhay-TA provides a modern, type-safe approach to technical analysis in Python. Built around immutable data structures and a powerful expression system, it enables complex indicator compositions through simple algebraic operations. The library emphasizes performance, type safety, and composability for both research and production environments.

## Architecture

### Immutable Data Models
- **`Bar`**: Immutable OHLCV price bars with timezone-aware timestamps and Decimal precision
- **`Series[T]`**: Generic time series with type safety for any data type, supporting indexing and slicing
- **`OHLCV`**: Columnar storage for efficient OHLCV data access with tuple-based immutability
- **`Dataset`**: Multi-symbol, multi-timeframe data collections with metadata tracking

### Expression System
The library implements a DAG-based expression system that enables mathematical composition of indicators:
```python
# Create indicator handles
sma_20 = ta.indicator("sma", period=20)
sma_50 = ta.indicator("sma", period=50)
rsi = ta.indicator("rsi", period=14)

# Compose expressions with operator overloading
signal = (sma_20 - sma_50) * rsi
crossover = sma_20 > sma_50
```

### Indicator Registry
Dynamic indicator registration with automatic schema generation and parameter validation:
```python
@ta.register("my_indicator")
def my_indicator(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    """Custom indicator with automatic parameter validation."""
    # Implementation here
    return result
```

### Built-in Indicators
- **Trend Analysis**: `sma`, `ema`, `macd`, `bbands` (Bollinger Bands)
- **Momentum Oscillators**: `rsi`, `stochastic`
- **Volatility Indicators**: `atr`
- **Volume Analysis**: `obv`, `vwap`

## Core API Reference

### Data Structures

#### Bar Creation
```python
from laakhay.ta import Bar, Price, Timestamp
from datetime import datetime, timezone

# Immutable OHLCV bar with Decimal precision
bar = Bar(
    ts=datetime(2024, 1, 1, tzinfo=timezone.utc),
    open=Price("100.0"),
    high=Price("105.0"),
    low=Price("95.0"),
    close=Price("102.0"),
    volume=Price("1000.0"),
    is_closed=True
)
```

#### Dataset Management
```python
# Multi-symbol, multi-timeframe data collections
dataset = ta.dataset([bar1, bar2, ...], symbol="BTCUSDT", timeframe="1h")

# Access series by key
price_series = dataset["close"]
volume_series = dataset["volume"]

# Filter by symbol/timeframe
btc_data = dataset.select(symbol="BTCUSDT")
hourly_data = dataset.select(timeframe="1h")
```

#### Series Operations
```python
# Generic time series with type safety
series = Series[Price](
    timestamps=(ts1, ts2, ts3),
    values=(Price("100"), Price("101"), Price("102")),
    symbol="BTCUSDT",
    timeframe="1h"
)

# Indexing and slicing
first_value = series[0]
recent_data = series[-10:]  # Last 10 points
time_slice = series.slice_by_time(start_time, end_time)
```

### Indicator System

#### Indicator Handles
```python
# Create parameterized indicator handles
sma_20 = ta.indicator("sma", period=20)
sma_50 = ta.indicator("sma", period=50)
rsi = ta.indicator("rsi", period=14)

# Execute against dataset
result = sma_20(dataset)

# Access schema information
schema = sma_20.schema
description = sma_20.describe()
```

#### Expression Composition
```python
# Mathematical composition with operator overloading
spread = sma_20 - sma_50
scaled_signal = spread * 2
normalized = spread / ta.literal(100)

# Comparison operations
crossover = sma_20 > sma_50
oversold = rsi < 30
combined_signal = crossover & oversold

# Complex expressions
trading_signal = (sma_20 - sma_50) * rsi / ta.literal(100)
```

#### Evaluation Engine
```python
# Direct expression evaluation
engine = ta.Engine()
result = engine.evaluate(expression, dataset)

# Cached evaluation for performance
cached_result = engine.evaluate(expression, dataset)  # Uses cache
```

### Data I/O

#### CSV Operations
```python
# Load OHLCV data from CSV
ohlcv = ta.from_csv(
    "data.csv", 
    symbol="BTCUSDT", 
    timeframe="1h",
    timestamp_col="timestamp",
    open_col="open",
    high_col="high",
    low_col="low",
    close_col="close",
    volume_col="volume"
)

# Load price series
price_series = ta.from_csv(
    "prices.csv", 
    symbol="ETHUSDT", 
    timeframe="1h", 
    value_col="price"
)

# Export results
ta.to_csv(result, "output.csv", value_col="signal_value")
```

#### Serialization
```python
# Convert to/from dictionaries
bar_dict = bar.to_dict()
bar_from_dict = Bar.from_dict(bar_dict)

series_dict = series.to_dict()
series_from_dict = Series.from_dict(series_dict)
```

## Usage Examples

### Basic Technical Analysis
```python
import laakhay.ta as ta
from laakhay.ta import Bar, Price
from datetime import datetime, timezone

# Create sample OHLCV data
bars = [
    Bar(ts=datetime(2024, 1, 1, tzinfo=timezone.utc), 
        open=Price("100"), high=Price("105"), low=Price("95"), 
        close=Price("102"), volume=Price("1000"), is_closed=True),
    Bar(ts=datetime(2024, 1, 2, tzinfo=timezone.utc), 
        open=Price("102"), high=Price("108"), low=Price("98"), 
        close=Price("106"), volume=Price("1200"), is_closed=True),
    # ... additional bars
]

# Create dataset
dataset = ta.dataset(bars, symbol="BTCUSDT", timeframe="1h")

# Create indicator handles
sma_20 = ta.indicator("sma", period=20)
sma_50 = ta.indicator("sma", period=50)
rsi = ta.indicator("rsi", period=14)

# Compose trading signal
signal = (sma_20 - sma_50) * rsi
result = signal(dataset)

print(f"Signal values: {result.values}")
```

### Custom Indicator Development
```python
@ta.register("exponential_sma")
def exponential_sma(ctx: SeriesContext, period: int = 20, alpha: float = 0.1) -> Series[Price]:
    """Custom exponential smoothing implementation."""
    source = ctx.price_series
    if len(source) == 0:
        return Series[Price](timestamps=(), values=(), 
                           symbol=source.symbol, timeframe=source.timeframe)
    
    values = [source.values[0]]
    for i in range(1, len(source)):
        smoothed = alpha * float(source.values[i]) + (1 - alpha) * float(values[-1])
        values.append(Price(smoothed))
    
    return Series[Price](
        timestamps=source.timestamps,
        values=tuple(values),
        symbol=source.symbol,
        timeframe=source.timeframe
    )
```

### Multi-timeframe Analysis
```python
# Create datasets for different timeframes
dataset_1h = ta.dataset(bars_1h, symbol="BTCUSDT", timeframe="1h")
dataset_5m = ta.dataset(bars_5m, symbol="BTCUSDT", timeframe="5m")

# Cross-timeframe signal composition
sma_1h = ta.indicator("sma", period=20)(dataset_1h)
sma_5m = ta.indicator("sma", period=20)(dataset_5m)

# Multi-timeframe trend confirmation
trend_confirmed = (sma_1h > sma_1h.shift(1)) & (sma_5m > sma_5m.shift(1))
```

### Performance Optimization
```python
# Use evaluation engine for complex expressions
engine = ta.Engine()

# Build complex expression graph
expression = (sma_20 - sma_50) / ta.literal(100) * rsi + ta.literal(50)

# Evaluate with caching
result = engine.evaluate(expression, dataset)

# Subsequent evaluations use cached intermediate results
result2 = engine.evaluate(expression, dataset)  # Uses cache
```

### Data Pipeline Integration
```python
# Load data from multiple sources
btc_data = ta.from_csv("btc_1h.csv", symbol="BTCUSDT", timeframe="1h")
eth_data = ta.from_csv("eth_1h.csv", symbol="ETHUSDT", timeframe="1h")

# Combine datasets
combined_dataset = ta.dataset(btc_data, eth_data)

# Calculate cross-asset signals
btc_sma = ta.indicator("sma", period=20)(combined_dataset.select(symbol="BTCUSDT"))
eth_sma = ta.indicator("sma", period=20)(combined_dataset.select(symbol="ETHUSDT"))

# Relative strength analysis
relative_strength = btc_sma / eth_sma
```

## Type System

The library provides comprehensive type safety through custom type aliases:

```python
from laakhay.ta import Price, Qty, Rate, Timestamp

# Type-safe price operations
price = Price("100.50")  # Decimal precision
qty = Qty("1000.0")      # Volume/quantity
rate = Rate("0.05")      # Percentage/rate values
ts = Timestamp(datetime.now(timezone.utc))  # Timezone-aware timestamps
```

## Performance Characteristics

- **Immutable Data Structures**: Tuple-based storage for memory efficiency
- **Decimal Precision**: Financial-grade precision for price calculations
- **Expression Caching**: Automatic caching of intermediate results
- **Type Safety**: Compile-time type checking with mypy/pyright
- **Memory Efficient**: Columnar storage for OHLCV data

## Requirements

- Python >= 3.12
- No external dependencies (pure Python implementation)
- Optional: numpy for accelerated computations (future enhancement)

## Installation

```bash
pip install laakhay-ta
```

## Development

```bash
git clone https://github.com/laakhay/ta
cd ta
pip install -e .
pytest
```

## License

MIT License

---

Built with ❤️ by [Laakhay](https://laakhay.com)
