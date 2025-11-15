# Laakhay TA

Laakhay TA is a stateless technical analysis toolkit built on immutable data structures, explicit indicator metadata, and algebraic composition. It provides a domain-specific language (DSL) for expressing trading strategies with support for multi-source data (OHLCV, trades, orderbook, liquidations), filtering, aggregation, and time-shifted queries.

## Highlights
- Immutable primitives: `Bar`, `OHLCV`, `Series`, and `Dataset` keep timezone-aware timestamps and Decimal precision for reproducible analytics.
- Registry-driven indicators: `ta.indicator("sma", ...)` exposes schemas, enforces parameters, and can be extended at runtime with `@ta.register`.
- Multi-source expressions: Access data from OHLCV, trades, orderbook, and liquidation sources with attribute chains like `BTC/USDT.trades.volume` or `binance.BTC.orderbook.imbalance`.
- DSL for strategies: Write Python-like expressions with filtering (`trades.filter(amount > 1_000_000).count`), aggregation (`trades.sum(amount)`), and time-shifts (`price.24h_ago`).
- Algebraic composition: indicator handles, literals, and sources build expression DAGs that support dependency inspection and streaming updates.
- Requirement planning: Expression planner computes data requirements, lookbacks, and serializes them for backend ingestion services.
- Deterministic alignment: `align_series` and availability masks make lookback requirements explicit and guard against silent truncation.
- I/O and streaming utilities: `ta.from_csv`/`ta.to_csv` bridge datasets, while `Stream` tracks expression readiness for live feeds.

## Requirements
- Python 3.12 or newer
- [`uv`](https://docs.astral.sh/uv/) is recommended for environment management

## Installation

```bash
uv pip install laakhay-ta
```

## Quick Start

```python
from datetime import UTC, datetime
from decimal import Decimal

import laakhay.ta as ta
from laakhay.ta import dataset
from laakhay.ta.core import OHLCV, align_series

ohlcv = OHLCV(
    timestamps=(
        datetime(2024, 1, 1, tzinfo=UTC),
        datetime(2024, 1, 2, tzinfo=UTC),
        datetime(2024, 1, 3, tzinfo=UTC),
        datetime(2024, 1, 4, tzinfo=UTC),
    ),
    opens=(Decimal("100"), Decimal("101"), Decimal("103"), Decimal("104")),
    highs=(Decimal("105"),) * 4,
    lows=(Decimal("99"),) * 4,
    closes=(Decimal("101"), Decimal("102"), Decimal("104"), Decimal("105")),
    volumes=(Decimal("1000"), Decimal("1100"), Decimal("1150"), Decimal("1200")),
    is_closed=(True,) * 4,
    symbol="BTCUSDT",
    timeframe="1h",
)

market = dataset(ohlcv)

sma_fast_handle = ta.indicator("sma", period=2)
sma_slow_handle = ta.indicator("sma", period=3)

sma_fast = sma_fast_handle(market)
sma_slow = sma_slow_handle(market)

fast, slow = align_series(
    sma_fast,
    sma_slow,
    how="inner",
    fill="none",
    symbol="BTCUSDT",
    timeframe="1h",
)
spread = fast - slow

print(spread.values)            # Decimal results
print(spread.availability_mask) # lookback readiness
```

Expression composition is available for analysis and tooling:

```python
signal = sma_fast_handle - sma_slow_handle
print(signal.describe())
requirements = signal.requirements()
```

## Multi-Source Expressions

Access data from multiple sources using attribute chains:

```python
from laakhay.ta.expr.dsl import parse_expression_text, compile_expression
from laakhay.ta.expr.runtime import preview, validate

# OHLCV data
expr = parse_expression_text("BTC/USDT.price > 50000")
expr = parse_expression_text("BTC/USDT.1h.volume > 1000000")

# Trade aggregations
expr = parse_expression_text("BTC/USDT.trades.volume > 1000000")
expr = parse_expression_text("BTC/USDT.trades.filter(amount > 1000000).count > 10")
expr = parse_expression_text("BTC/USDT.trades.sum(amount) > 50000000")

# Orderbook data
expr = parse_expression_text("BTC/USDT.orderbook.imbalance > 0.5")
expr = parse_expression_text("binance.BTC.orderbook.spread_bps < 10")

# Time-shifted queries
expr = parse_expression_text("BTC/USDT.price.24h_ago < BTC/USDT.price")
expr = parse_expression_text("BTC/USDT.volume.change_pct_24h > 10")

# Validate and preview expressions
result = validate(expr)
if result.valid:
    preview_result = preview(expr, bars=your_bars, symbol="BTC/USDT", timeframe="1h")
    print(preview_result.triggers)
```

## Expression Planning and Requirements

The planner computes data requirements for expressions:

```python
from laakhay.ta.expr.planner import plan_expression, generate_capability_manifest
from laakhay.ta.expr.dsl import compile_expression

expr = compile_expression("BTC/USDT.trades.filter(amount > 1000000).count > 10")
plan = plan_expression(expr.root)

# Access requirements
print(plan.requirements.data_requirements)  # Data sources needed
print(plan.requirements.required_sources)    # ['trades']
print(plan.requirements.required_exchanges)  # ['binance'] if specified

# Serialize for backend
plan_dict = plan.to_dict()

# Generate capability manifest for API
manifest = generate_capability_manifest()
print(manifest["sources"])      # Available sources and fields
print(manifest["indicators"])   # Available indicators
print(manifest["operators"])    # Available operators
```

Inspect indicator metadata or register custom logic:

```python
from laakhay.ta import SeriesContext, register

schema = ta.describe_indicator("sma")
print(schema.params)

@register("mid_price")
def mid_price(ctx: SeriesContext):
    return (ctx.high + ctx.low) / 2
```

## Streaming and I/O

```python
from datetime import UTC, datetime, timedelta

from laakhay.ta import ta
from laakhay.ta.core.bar import Bar
from laakhay.ta.stream import Stream

stream = Stream()
stream.register("sma2", ta.indicator("sma", period=2)._to_expression())

base = datetime(2024, 1, 1, tzinfo=UTC)
stream.update_ohlcv("BTCUSDT", "1h", Bar.from_raw(base, 100, 100, 100, 100, 1, True))
update = stream.update_ohlcv(
    "BTCUSDT",
    "1h",
    Bar.from_raw(base + timedelta(hours=1), 110, 110, 110, 110, 1, True),
)

print(update.transitions[0].value)  # Decimal('105')
```

CSV helpers round-trip datasets:

```python
ohlcv = ta.from_csv("btc_1h.csv", symbol="BTCUSDT", timeframe="1h")
ta.to_csv(ohlcv, "btc_out.csv")
```

## Development

```bash
git clone https://github.com/laakhay/ta
cd ta
uv sync --extra dev
uv run ruff format laakhay/
uv run ruff check --fix laakhay/
PYTHONPATH=$PWD uv run pytest tests/ -v --tb=short
```

## License

MIT License
