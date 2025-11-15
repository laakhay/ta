# Laakhay TA

A stateless technical analysis toolkit built on immutable data structures, explicit indicator metadata, and algebraic composition. Provides a domain-specific language (DSL) for expressing trading strategies with support for multi-source data (OHLCV, trades, orderbook, liquidations), filtering, aggregation, time-shifted queries, and **explicit indicator input sources**.

## Core Principles

- **Immutable & Stateless**: All data structures (`Bar`, `OHLCV`, `Series`, `Dataset`) are immutable with timezone-aware timestamps and Decimal precision
- **Registry-Driven**: Indicators expose schemas, enforce parameters, and can be extended at runtime
- **Algebraic Composition**: Indicators, literals, and sources compose into expression DAGs with dependency inspection
- **Multi-Source Support**: Access data from OHLCV, trades, orderbook, and liquidation sources
- **Explicit Input Sources**: Indicators can operate on arbitrary series specified in expressions
- **Requirement Planning**: Expression planner computes data requirements, lookbacks, and serializes them for backend services

## Installation

```bash
uv pip install laakhay-ta
```

**Requirements**: Python 3.12+

## Quick Start

### Basic Indicator Usage

```python
from datetime import UTC, datetime
from decimal import Decimal

import laakhay.ta as ta
from laakhay.ta import dataset
from laakhay.ta.core import OHLCV, align_series

# Create OHLCV data
ohlcv = OHLCV(
    timestamps=(
        datetime(2024, 1, 1, tzinfo=UTC),
        datetime(2024, 1, 2, tzinfo=UTC),
        datetime(2024, 1, 3, tzinfo=UTC),
    ),
    opens=(Decimal("100"), Decimal("101"), Decimal("103")),
    highs=(Decimal("105"),) * 3,
    lows=(Decimal("99"),) * 3,
    closes=(Decimal("101"), Decimal("102"), Decimal("104")),
    volumes=(Decimal("1000"), Decimal("1100"), Decimal("1150")),
    is_closed=(True,) * 3,
    symbol="BTCUSDT",
    timeframe="1h",
)

market = dataset(ohlcv)

# Create indicator handles
sma_fast = ta.indicator("sma", period=2)
sma_slow = ta.indicator("sma", period=3)

# Evaluate on dataset
fast_series = sma_fast(market)
slow_series = sma_slow(market)

# Align and compute
fast, slow = align_series(fast_series, slow_series, how="inner", fill="none", 
                          symbol="BTCUSDT", timeframe="1h")
spread = fast - slow

print(spread.values)  # Decimal results
```

### Expression Composition

```python
# Compose indicators algebraically
signal = sma_fast - sma_slow
result = signal.run(market)

# Inspect requirements
print(signal.describe())
requirements = signal.requirements()
print(requirements.fields)  # Required data fields
```

## Indicator Expression Inputs

**New Feature**: Indicators can now operate on explicit series specified in expressions, enabling operations on arbitrary data sources.

### Explicit Source Syntax

```python
from laakhay.ta.expr.dsl import compile_expression

# OHLCV sources
expr = compile_expression("sma(BTC.price, period=20)")
expr = compile_expression("sma(BTC.volume, period=10)")

# Non-OHLCV sources (trades, orderbook, liquidations)
expr = compile_expression("sma(BTC.trades.volume, period=20)")
expr = compile_expression("sma(binance.BTC.orderbook.imbalance, period=10)")
expr = compile_expression("sma(BTC.liquidation.volume, period=5)")

# Nested expressions
expr = compile_expression("sma(BTC.high + BTC.low, period=5)")
expr = compile_expression("rsi(BTC.trades.avg_price, period=14)")

# Evaluate expressions
result = expr.run(dataset)
```

### Programmatic API

```python
from laakhay.ta.core import Series
from decimal import Decimal

# Create a custom series
custom_series = Series(
    timestamps=(datetime(2024, 1, 1, tzinfo=UTC),),
    values=(Decimal("100"),),
    symbol="BTCUSDT",
    timeframe="1h"
)

# Use as input_series parameter
sma_handle = ta.sma(input_series=custom_series, period=20)
result = sma_handle.run(market)
```

### Backward Compatibility

Traditional syntax continues to work:

```python
# These all work as before
expr = compile_expression("sma(20)")  # Uses default 'close' field
expr = compile_expression("sma(period=20)")  # Keyword arguments
expr = compile_expression("rsi(14)")  # RSI with default close
```

## Multi-Source Expressions

Access data from multiple sources using attribute chains:

### OHLCV Data

```python
from laakhay.ta.expr.dsl import parse_expression_text, compile_expression

# Price and volume
expr = parse_expression_text("BTC/USDT.price > 50000")
expr = parse_expression_text("BTC/USDT.1h.volume > 1000000")

# Multiple timeframes
expr = parse_expression_text("BTC/USDT.1h.price > BTC/USDT.4h.price")
```

### Trade Aggregations

```python
# Volume and count
expr = parse_expression_text("BTC/USDT.trades.volume > 1000000")
expr = parse_expression_text("BTC/USDT.trades.count > 100")

# Filtered aggregations
expr = parse_expression_text("BTC/USDT.trades.filter(amount > 1000000).count > 10")
expr = parse_expression_text("BTC/USDT.trades.sum(amount) > 50000000")
expr = parse_expression_text("BTC/USDT.trades.avg(price) > 50000")

# Aggregation properties
expr = parse_expression_text("BTC/USDT.trades.count > 100")
```

### Orderbook Data

```python
# Imbalance and spread
expr = parse_expression_text("BTC/USDT.orderbook.imbalance > 0.5")
expr = parse_expression_text("binance.BTC.orderbook.spread_bps < 10")
expr = parse_expression_text("BTC/USDT.orderbook.pressure > 0.7")

# Depth analysis
expr = parse_expression_text("BTC/USDT.orderbook.bid_depth > BTC/USDT.orderbook.ask_depth")
```

### Time-Shifted Queries

```python
# Historical comparisons
expr = parse_expression_text("BTC/USDT.price.24h_ago < BTC/USDT.price")
expr = parse_expression_text("BTC/USDT.volume.change_pct_24h > 10")
expr = parse_expression_text("BTC/USDT.price.change_1h > 0")
```

### Exchange and Timeframe Qualifiers

```python
# Exchange-specific data
expr = parse_expression_text("binance.BTC.price > 50000")
expr = parse_expression_text("bybit.BTC.1h.trades.volume > 1000000")

# Timeframe specification
expr = parse_expression_text("BTC.1h.price > BTC.4h.price")
expr = parse_expression_text("binance.BTC.1h.orderbook.imbalance")
```

## Expression Planning and Requirements

The planner computes data requirements, lookbacks, and dependencies:

```python
from laakhay.ta.expr.planner import plan_expression
from laakhay.ta.expr.dsl import compile_expression

# Compile expression
expr = compile_expression("sma(BTC.trades.volume, period=20) > 1000000")
plan = plan_expression(expr._node)

# Access requirements
print(plan.requirements.data_requirements)  # Data sources needed
print(plan.requirements.required_sources)    # ['trades']
print(plan.requirements.required_exchanges)  # ['binance'] if specified
print(plan.requirements.fields)              # Field requirements

# Serialize for backend
plan_dict = plan.to_dict()
```

### Capability Manifest

```python
from laakhay.ta.expr.planner import generate_capability_manifest

manifest = generate_capability_manifest()
print(manifest["sources"])      # Available sources and fields
print(manifest["indicators"])   # Available indicators with metadata
print(manifest["operators"])    # Available operators
```

## Indicator Registry

### Inspecting Indicators

```python
# Get indicator schema
schema = ta.describe_indicator("sma")
print(schema.params)           # Parameter definitions
print(schema.metadata)          # Metadata (lookback, fields, etc.)
print(schema.description)       # Documentation

# Check input field metadata
metadata = schema.metadata
print(metadata.input_field)           # Default input field ('close')
print(metadata.input_series_param)   # Parameter name for override ('input_series')
```

### Registering Custom Indicators

```python
from laakhay.ta import SeriesContext, register, Series, Price

@register("mid_price", description="Mid price indicator")
def mid_price(ctx: SeriesContext) -> Series[Price]:
    """Compute mid price from high and low."""
    return (ctx.high + ctx.low) / 2

# Use custom indicator
mid = ta.indicator("mid_price")
result = mid(market)
```

### Indicator Metadata

Indicators declare their metadata including:
- **Required fields**: Fields needed from context (e.g., `('close',)`)
- **Optional fields**: Additional fields that may be used
- **Lookback parameters**: Parameters that affect lookback window
- **Input field**: Default input field (e.g., `'close'`)
- **Input series parameter**: Parameter name for explicit input override

## Streaming and Real-Time Updates

```python
from laakhay.ta.stream import Stream
from laakhay.ta.core.bar import Bar

# Create stream
stream = Stream()
stream.register("sma2", ta.indicator("sma", period=2)._to_expression())

# Update with new bars
base = datetime(2024, 1, 1, tzinfo=UTC)
stream.update_ohlcv("BTCUSDT", "1h", 
    Bar.from_raw(base, 100, 105, 99, 101, 1000, True))
    
update = stream.update_ohlcv("BTCUSDT", "1h",
    Bar.from_raw(base + timedelta(hours=1), 101, 106, 100, 102, 1100, True))

print(update.transitions[0].value)  # Updated indicator value
```

## I/O and Data Loading

### CSV Import/Export

```python
# Load from CSV
ohlcv = ta.from_csv("btc_1h.csv", symbol="BTCUSDT", timeframe="1h")
market = dataset(ohlcv)

# Export to CSV
ta.to_csv(ohlcv, "btc_out.csv")
```

### Dataset Construction

```python
from laakhay.ta import dataset

# Single series
market = dataset(ohlcv)

# Multiple series
market = dataset(btc_ohlcv, eth_ohlcv)

# With trades/orderbook data
market = dataset(ohlcv, trades_series, orderbook_series)
```

## Expression Validation and Preview

```python
from laakhay.ta.expr.runtime import validate, preview

# Validate expression syntax and requirements
expr = compile_expression("sma(BTC.price, period=20) > sma(BTC.price, period=50)")
result = validate(expr)

if result.valid:
    print("Expression is valid")
    print(result.requirements)
else:
    print(result.errors)

# Preview expression execution
preview_result = preview(expr, bars=your_bars, symbol="BTC/USDT", timeframe="1h")
print(preview_result.triggers)
print(preview_result.values)
```

## Advanced Features

### Complex Expressions

```python
# Multiple indicators with explicit sources
expr = compile_expression(
    "sma(BTC.price, period=20) > sma(BTC.volume, period=10) & "
    "rsi(BTC.trades.avg_price, period=14) < 30"
)

# Nested operations
expr = compile_expression(
    "sma(BTC.high + BTC.low, period=5) > "
    "sma(BTC.trades.volume, period=20)"
)

# Time-shifted comparisons
expr = compile_expression(
    "sma(BTC.price, period=20) > BTC.price.24h_ago"
)
```

### Expression Serialization

```python
from laakhay.ta.expr.dsl.nodes import expression_to_dict, expression_from_dict

# Serialize expression
expr = parse_expression_text("sma(BTC.price, period=20)")
serialized = expression_to_dict(expr)

# Deserialize
restored = expression_from_dict(serialized)
```

## Architecture

### Core Components

| Component | Responsibility |
|-----------|---------------|
| **Core Data** | Immutable series (`Bar`, `OHLCV`, `Series`) with timezone-aware timestamps |
| **Expression DSL** | Parser and AST for strategy expressions |
| **Indicator Registry** | Metadata-driven indicator system with schema validation |
| **Planner** | Computes data requirements, lookbacks, and dependencies |
| **Evaluator** | Executes expression graphs on datasets |
| **Streaming** | Real-time update processing |

### Expression Graph

Expressions compile to a directed acyclic graph (DAG) where:
- **Nodes** represent operations (indicators, arithmetic, comparisons)
- **Edges** represent data dependencies
- **Source nodes** represent data requirements (OHLCV, trades, etc.)
- **Indicator nodes** can have explicit input expressions as dependencies

### Data Flow

1. **Parse**: Expression text → AST nodes
2. **Compile**: AST nodes → Expression graph
3. **Plan**: Expression graph → Requirements and dependencies
4. **Evaluate**: Expression graph + Dataset → Results

## Development

```bash
# Clone repository
git clone https://github.com/laakhay/ta
cd ta

# Setup environment
uv sync --extra dev

# Format code
uv run ruff format laakhay/

# Lint
uv run ruff check --fix laakhay/

# Run tests
PYTHONPATH=$PWD uv run pytest tests/ -v --tb=short
```

## License

MIT License
