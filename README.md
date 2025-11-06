# Laakhay TA

Laakhay TA is a stateless technical analysis toolkit built on immutable data structures, explicit indicator metadata, and algebraic composition.

## Highlights
- Immutable primitives: `Bar`, `OHLCV`, `Series`, and `Dataset` keep timezone-aware timestamps and Decimal precision for reproducible analytics.
- Registry-driven indicators: `ta.indicator("sma", ...)` exposes schemas, enforces parameters, and can be extended at runtime with `@ta.register`.
- Algebraic composition: indicator handles, literals, and sources build expression DAGs that support dependency inspection and streaming updates.
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
uv run ruff check laakhay/
PYTHONPATH=$PWD uv run pytest tests/ -v --tb=short
```

## License

MIT License
