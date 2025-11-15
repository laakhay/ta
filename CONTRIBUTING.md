# Contributing to Laakhay-TA

## Setup
```bash
git clone https://github.com/laakhay/ta
cd ta
uv sync --extra dev
```

## Development
```bash
# Format and lint
uv run ruff format laakhay/
uv run ruff check --fix laakhay/

# Test
uv run pytest tests/ -v

# Type check (if available)
uv run pyright laakhay/ta/
```

## Adding Indicators
```python
# laakhay/ta/indicators/trend/my_indicator.py
from ...core import Series
from ...core.types import Price
from ...registry.models import SeriesContext
from ...registry.registry import register

@register("my_indicator")
def my_indicator(ctx: SeriesContext, period: int = 20) -> Series[Price]:
    """My custom indicator."""
    source = ctx.price_series
    # Implementation
    return result
```

## Expression System

The expression system supports multi-source data access, filtering, aggregation, and time-shifts:

- **Attribute chains**: `BTC/USDT.trades.volume`, `binance.BTC.orderbook.imbalance`
- **Filters**: `trades.filter(amount > 1_000_000).count`
- **Aggregations**: `trades.sum(amount)`, `trades.avg(price)`
- **Time-shifts**: `price.24h_ago`, `volume.change_pct_24h`

When adding new features:
- Update parser in `laakhay/ta/expr/dsl/parser.py` for new syntax
- Add AST nodes in `laakhay/ta/expr/dsl/nodes.py`
- Update compiler in `laakhay/ta/expr/dsl/compiler.py`
- Add expression models in `laakhay/ta/expr/algebra/models.py`
- Update planner in `laakhay/ta/expr/planner/planner.py` for requirement computation
- Update manifest in `laakhay/ta/expr/planner/manifest.py` if adding new sources/fields

## Commit Format
```
type(scope): description

feat(indicators): add MACD indicator
feat(expr): add filter and aggregation support
fix(series): handle empty series
refactor(planner): make manifest data-driven
docs: update README
```

Common scopes: `indicators`, `expr`, `planner`, `core`, `data`, `registry`

## PR Requirements
- All tests pass
- Code formatted with ruff
- Type hints complete
- Tests for new features

## Getting Help
- [Issues](https://github.com/laakhay/ta/issues)
- laakhay.corp@gmail.com
