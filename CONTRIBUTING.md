# Contributing to Laakhay-TA

## Setup
```bash
git clone https://github.com/laakhay/ta
cd ta
pip install -e ".[dev]"
```

## Development
```bash
# Format and lint
ruff format . && ruff check . --fix

# Test
pytest

# Type check
pyright laakhay/ta/
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

## Commit Format
```
type(scope): description

feat(indicators): add MACD indicator
fix(series): handle empty series
docs: update README
```

## PR Requirements
- All tests pass
- Code formatted with ruff
- Type hints complete
- Tests for new features

## Getting Help
- [Issues](https://github.com/laakhay/ta/issues)
- laakhay.corp@gmail.com
