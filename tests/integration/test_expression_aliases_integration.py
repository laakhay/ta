from datetime import UTC, datetime, timedelta

from laakhay.ta.core.bar import Bar
from laakhay.ta.core.dataset import Dataset
from laakhay.ta.core.ohlcv import OHLCV
from laakhay.ta.expr.dsl import compile_expression


def create_simple_dataset() -> Dataset:
    """Create a simple OHLCV dataset."""
    base = datetime(2024, 1, 1, tzinfo=UTC)
    bars = [
        Bar.from_raw(base + timedelta(hours=i), 100 + i, 101 + i, 99 + i, 100 + i, 1000 + i * 100, True)
        for i in range(50)
    ]
    ohlcv = OHLCV.from_bars(bars, symbol="BTCUSDT", timeframe="1h")
    ds = Dataset()
    ds.add_series("BTCUSDT", "1h", ohlcv, source="ohlcv")
    return ds


def test_integration_mean_alias_compiles():
    """Test that compiling an expression with 'mean' succeeds."""
    expr = compile_expression("mean(close, lookback=10)")
    assert expr is not None


def test_integration_median_alias_compiles():
    """Test that compiling an expression with 'median' succeeds."""
    expr = compile_expression("median(close, lookback=10)")
    assert expr is not None


def test_integration_lookback_keyword_works():
    """Test integration behavior of 'lookback' keyword."""
    ds = create_simple_dataset()
    expr = compile_expression("sma(close, lookback=10)")
    result = expr.run(ds)
    # Result should be produced
    series = result[("BTCUSDT", "1h", "default")]
    assert len(series.values) > 0


def test_integration_volume_mean_compiles():
    """Test volume-based mean compiles (execution might fail until primitive update)."""
    # This should now compile because 'mean' is 'rolling_mean'
    # and 'volume' is a valid input expression.
    expr = compile_expression("mean(volume, lookback=10)")
    assert expr is not None
